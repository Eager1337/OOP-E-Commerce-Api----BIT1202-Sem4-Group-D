"""
Order router.
CRUD operations for customer orders with coupon/discount support.
All prices in Sierra Leonean Leone (Le / SLL).
"""
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, OrderItem, Product, OrderStatus, User, Coupon, DiscountType
from app.auth import get_current_user, require_manager_or_admin
from app.schemas import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


def generate_order_number() -> str:
    """Generate a unique order number."""
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


def _apply_coupon(coupon: Coupon, total: float) -> tuple[float, float]:
    """
    Apply coupon discount. Returns (discount_amount, new_total).
    """
    if coupon.discount_type == DiscountType.percentage:
        discount = round(total * (coupon.discount_value / 100), 0)
    else:
        discount = min(coupon.discount_value, total)
    new_total = max(0.0, total - discount)
    return discount, new_total


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: OrderStatus = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List orders.
    - Admins/Managers see all orders
    - Viewers see only their own orders
    """
    query = db.query(Order)

    if current_user.role.value == "viewer":
        query = query.filter(Order.user_id == current_user.id)

    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    pages = (total + limit - 1) // limit if limit > 0 else 1

    return OrderListResponse(
        items=orders,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        pages=pages,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role.value == "viewer" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this order")

    return order


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new order with automatic stock deduction.

    - **items**: List of products and quantities
    - **shipping_address**: Delivery address in Sierra Leone
    - **coupon_code**: Optional discount coupon (e.g. `SAVE10`)
    - **notes**: Optional delivery notes

    Prices and totals are in **Sierra Leonean Leone (Le)**.
    """
    total_amount = 0.0
    order_items = []

    for item in order_data.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.is_active == True,
        ).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product ID {item.product_id} not found or inactive",
            )

        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.quantity}",
            )

        subtotal = product.price * item.quantity
        total_amount += subtotal
        order_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": product.price,
            "subtotal": subtotal,
        })
        product.quantity -= item.quantity

    # Apply coupon if provided
    discount_amount = 0.0
    coupon_id = None
    coupon_code = order_data.coupon_code

    if coupon_code:
        coupon = db.query(Coupon).filter(Coupon.code == coupon_code.upper()).first()
        if not coupon or not coupon.is_active:
            raise HTTPException(status_code=400, detail="Invalid or inactive coupon code")
        if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Coupon has expired")
        if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")
        if total_amount < coupon.min_order_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum order amount for this coupon is Le {coupon.min_order_amount:,.0f}",
            )

        discount_amount, total_amount = _apply_coupon(coupon, total_amount)
        coupon.times_used += 1
        coupon_id = coupon.id

    db_order = Order(
        order_number=generate_order_number(),
        user_id=current_user.id,
        coupon_id=coupon_id,
        total_amount=total_amount,
        discount_amount=discount_amount,
        shipping_address=order_data.shipping_address,
        notes=order_data.notes,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item_data in order_items:
        db.add(OrderItem(order_id=db_order.id, **item_data))

    db.commit()
    db.refresh(db_order)
    return db_order


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
):
    """Update order status (Manager/Admin only)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    for field, value in order_update.model_dump(exclude_unset=True).items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
):
    """Cancel and delete an order, restoring stock (Manager/Admin only)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status in [OrderStatus.pending, OrderStatus.processing]:
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.quantity += item.quantity

    db.delete(order)
    db.commit()
    return None
