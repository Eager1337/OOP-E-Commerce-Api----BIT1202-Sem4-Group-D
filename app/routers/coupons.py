"""
Coupon router — create and apply discount codes.
Supports percentage and fixed Sierra Leonean Leone (Le) discounts.
"""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Coupon, DiscountType
from app.auth import require_admin, require_manager_or_admin, get_current_user
from app.schemas import CouponCreate, CouponUpdate, CouponResponse, CouponValidateResponse

router = APIRouter(prefix="/coupons", tags=["Coupons & Discounts"])


def _check_coupon_valid(coupon: Coupon, order_amount: float = 0.0) -> tuple[bool, str]:
    """Internal helper: check if a coupon is valid."""
    if not coupon.is_active:
        return False, "Coupon is not active"
    if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
        return False, "Coupon has expired"
    if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
        return False, "Coupon usage limit has been reached"
    if order_amount < coupon.min_order_amount:
        return False, f"Minimum order amount is Le {coupon.min_order_amount:,.0f}"
    return True, "Coupon is valid"


@router.get("/", response_model=List[CouponResponse])
async def list_coupons(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """List all coupons (Manager/Admin only)."""
    query = db.query(Coupon)
    if active_only:
        query = query.filter(Coupon.is_active == True)
    return query.all()


@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Create a discount coupon (Admin only).

    - **percentage**: `discount_value=10` means 10% off
    - **fixed**: `discount_value=50000` means Le 50,000 off

    Example coupon codes: `WELCOME10`, `FREETOWN20`, `SAVE50000`
    """
    existing = db.query(Coupon).filter(Coupon.code == coupon_data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")

    coupon = Coupon(**{**coupon_data.model_dump(), "code": coupon_data.code.upper()})
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.get("/validate/{code}", response_model=CouponValidateResponse)
async def validate_coupon(
    code: str,
    order_amount: float = Query(0.0, ge=0, description="Order total in Le to check min amount"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Validate a coupon code before applying it to an order.

    Returns whether the coupon is valid and the discount details.
    """
    coupon = db.query(Coupon).filter(Coupon.code == code.upper()).first()
    if not coupon:
        return CouponValidateResponse(valid=False, message="Coupon code not found")

    valid, message = _check_coupon_valid(coupon, order_amount)
    if not valid:
        return CouponValidateResponse(valid=False, message=message)

    return CouponValidateResponse(
        valid=True,
        message=message,
        discount_type=coupon.discount_type.value,
        discount_value=coupon.discount_value,
        coupon_id=coupon.id,
    )


@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """Get coupon details by ID (Manager/Admin only)."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon


@router.put("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: int,
    coupon_update: CouponUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Update a coupon (Admin only)."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    for field, value in coupon_update.model_dump(exclude_unset=True).items():
        setattr(coupon, field, value)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Deactivate a coupon (Admin only)."""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    coupon.is_active = False
    db.commit()
    return None
