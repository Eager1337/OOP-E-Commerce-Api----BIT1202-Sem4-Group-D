"""
Product router.
CRUD operations and inventory management for products.
Demonstrates async/await for I/O-bound tasks.
"""
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Product, Category, OrderItem
from app.auth import require_manager_or_admin, get_current_user
from app.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, 
    ProductListResponse, InventoryAlert
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None, max_length=100),
    in_stock: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all products with filtering and pagination.

    - **skip**: Number of records to skip
    - **limit**: Records per page
    - **category_id**: Filter by category
    - **min_price/max_price**: Price range filter
    - **search**: Search in name and description
    - **in_stock**: Filter by stock availability
    """
    query = db.query(Product)

    # Apply filters
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) | 
            (Product.description.ilike(search_term))
        )
    if in_stock is not None:
        if in_stock:
            query = query.filter(Product.quantity > 0)
        else:
            query = query.filter(Product.quantity == 0)

    total = query.count()
    products = query.offset(skip).limit(limit).all()
    pages = (total + limit - 1) // limit if limit > 0 else 1

    return ProductListResponse(
        items=products,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        pages=pages
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_manager_or_admin)
):
    """
    Create a new product (Manager/Admin only).

    - **name**: Product name
    - **sku**: Unique stock keeping unit
    - **price**: Selling price
    - **quantity**: Initial stock quantity
    - **category_id**: Associated category
    """
    # Check SKU uniqueness
    existing = db.query(Product).filter(Product.sku == product_data.sku).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists"
        )

    # Validate category exists
    if product_data.category_id:
        category = db.query(Category).filter(Category.id == product_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )

    db_product = Product(**product_data.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_manager_or_admin)
):
    """Update a product (Manager/Admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_manager_or_admin)
):
    """Delete a product (Manager/Admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()
    return None


@router.get("/inventory/alerts", response_model=List[InventoryAlert])
async def get_inventory_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(require_manager_or_admin)
):
    """
    Get low inventory alerts (Manager/Admin only).
    Returns products with quantity below reorder level.
    """
    low_stock = db.query(Product).filter(
        Product.quantity <= Product.reorder_level,
        Product.is_active == True
    ).all()

    alerts = [
        InventoryAlert(
            product_id=p.id,
            product_name=p.name,
            current_quantity=p.quantity,
            reorder_level=p.reorder_level
        )
        for p in low_stock
    ]
    return alerts


@router.post("/{product_id}/restock", response_model=ProductResponse)
async def restock_product(
    product_id: int,
    amount: int = Query(..., gt=0, description="Quantity to add"),
    db: Session = Depends(get_db),
    current_user = Depends(require_manager_or_admin)
):
    """
    Restock a product by adding quantity (Manager/Admin only).

    - **amount**: Number of units to add to inventory
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    product.quantity += amount
    db.commit()
    db.refresh(product)
    return product


# Async I/O-bound task demonstration
async def _send_restock_notification(product_name: str, amount: int) -> None:
    """
    Simulate sending a restock notification.
    Demonstrates async/await for I/O-bound tasks.
    """
    await asyncio.sleep(0.5)  # Simulate network delay
    print(f"[NOTIFICATION] Product '{product_name}' restocked with {amount} units")


@router.post("/{product_id}/restock-async", response_model=ProductResponse)
async def restock_product_async(
    product_id: int,
    amount: int = Query(..., gt=0),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_manager_or_admin)
):
    """
    Restock product with async notification (Manager/Admin only).
    Demonstrates async/await for I/O-bound operations.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    product.quantity += amount
    db.commit()
    db.refresh(product)

    # Async I/O operation
    await _send_restock_notification(product.name, amount)

    return product


@router.get("/stats/overview")
async def get_product_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_manager_or_admin)
):
    """Get product inventory statistics (Manager/Admin only)."""
    total_products = db.query(Product).count()
    total_value = db.query(func.sum(Product.price * Product.quantity)).scalar() or 0
    low_stock_count = db.query(Product).filter(
        Product.quantity <= Product.reorder_level
    ).count()
    out_of_stock = db.query(Product).filter(Product.quantity == 0).count()

    return {
        "total_products": total_products,
        "inventory_value": round(float(total_value), 2),
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock,
        "healthy_stock": total_products - low_stock_count
    }
