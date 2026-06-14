"""
Analytics router — sales reports, revenue analysis, and business intelligence.
All monetary values in Sierra Leonean Leone (Le / SLL).
"""
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models import Order, OrderItem, Product, Category, OrderStatus
from app.auth import require_manager_or_admin
from app.schemas import AnalyticsSummary, DailySales, TopProduct, CategoryRevenue

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_sales_summary(
    days: int = Query(30, ge=1, le=365, description="Number of past days to analyse"),
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """
    Sales summary for the last N days (Manager/Admin only).

    Returns:
    - Total revenue and order count
    - Average order value
    - Daily revenue breakdown
    - Top 5 best-selling products
    - Revenue by category
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Base query: completed/delivered orders only
    completed = [OrderStatus.processing, OrderStatus.shipped, OrderStatus.delivered]
    orders = (
        db.query(Order)
        .filter(Order.created_at >= since, Order.status.in_(completed))
        .all()
    )

    total_revenue = sum(o.total_amount for o in orders)
    total_orders = len(orders)
    avg_order = round(total_revenue / total_orders, 0) if total_orders else 0.0

    # Daily sales breakdown
    daily: dict[str, dict] = {}
    for o in orders:
        day = o.created_at.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {"orders": 0, "revenue": 0.0}
        daily[day]["orders"] += 1
        daily[day]["revenue"] += o.total_amount

    daily_sales = [
        DailySales(date=d, orders=v["orders"], revenue=round(v["revenue"], 0))
        for d, v in sorted(daily.items())
    ]

    # Top 5 products by quantity sold
    top_rows = (
        db.query(
            Product.id,
            Product.name,
            func.sum(OrderItem.quantity).label("total_sold"),
            func.sum(OrderItem.subtotal).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= since, Order.status.in_(completed))
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    top_products = [
        TopProduct(
            product_id=r.id,
            product_name=r.name,
            total_sold=r.total_sold or 0,
            total_revenue=round(r.total_revenue or 0, 0),
        )
        for r in top_rows
    ]

    # Revenue by category
    cat_rows = (
        db.query(
            Category.id,
            Category.name,
            func.sum(OrderItem.subtotal).label("revenue"),
            func.count(func.distinct(Order.id)).label("order_count"),
        )
        .join(Product, Product.category_id == Category.id)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= since, Order.status.in_(completed))
        .group_by(Category.id, Category.name)
        .order_by(func.sum(OrderItem.subtotal).desc())
        .all()
    )

    # Uncategorized products
    uncat_revenue = (
        db.query(func.sum(OrderItem.subtotal))
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Order.created_at >= since,
            Order.status.in_(completed),
            Product.category_id == None,
        )
        .scalar() or 0.0
    )

    revenue_by_cat = [
        CategoryRevenue(
            category_id=r.id,
            category_name=r.name,
            total_revenue=round(r.revenue or 0, 0),
            order_count=r.order_count or 0,
        )
        for r in cat_rows
    ]
    if uncat_revenue > 0:
        revenue_by_cat.append(CategoryRevenue(
            category_id=None,
            category_name="Uncategorized",
            total_revenue=round(uncat_revenue, 0),
            order_count=0,
        ))

    total_items = sum(r.total_sold for r in top_rows) if top_rows else 0

    return AnalyticsSummary(
        period=f"Last {days} days",
        total_revenue=round(total_revenue, 0),
        total_orders=total_orders,
        average_order_value=avg_order,
        total_items_sold=total_items,
        top_products=top_products,
        daily_sales=daily_sales,
        revenue_by_category=revenue_by_cat,
    )


@router.get("/profit-margins")
async def get_profit_margins(
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """
    Profit margin report for all active products (Manager/Admin only).

    Shows selling price, cost price, profit per unit, and margin percentage.
    All values in Sierra Leonean Leone (Le).
    """
    products = (
        db.query(Product)
        .filter(Product.is_active == True, Product.cost_price != None)
        .all()
    )

    results = []
    for p in products:
        profit = p.price - p.cost_price
        margin = (profit / p.price * 100) if p.price else 0
        results.append({
            "product_id": p.id,
            "product_name": p.name,
            "sku": p.sku,
            "selling_price_le": p.price,
            "cost_price_le": p.cost_price,
            "profit_per_unit_le": round(profit, 0),
            "margin_percent": round(margin, 1),
            "stock_value_le": round(p.price * p.quantity, 0),
            "currency": "SLL",
        })

    results.sort(key=lambda x: x["margin_percent"], reverse=True)
    return {
        "currency": "SLL",
        "currency_symbol": "Le",
        "products": results,
        "total_products_analysed": len(results),
    }


@router.get("/low-revenue-risk")
async def get_low_revenue_risk(
    db: Session = Depends(get_db),
    current_user=Depends(require_manager_or_admin),
):
    """
    Products at risk of zero revenue: low stock AND low sales (Manager/Admin only).
    Helps identify items to reorder or discontinue.
    """
    products = db.query(Product).filter(
        Product.is_active == True,
        Product.quantity <= Product.reorder_level,
    ).all()

    at_risk = []
    for p in products:
        total_sold = (
            db.query(func.sum(OrderItem.quantity))
            .filter(OrderItem.product_id == p.id)
            .scalar() or 0
        )
        at_risk.append({
            "product_id": p.id,
            "product_name": p.name,
            "sku": p.sku,
            "current_stock": p.quantity,
            "reorder_level": p.reorder_level,
            "total_units_sold_ever": total_sold,
            "price_le": p.price,
            "potential_revenue_at_risk_le": round(p.price * p.quantity, 0),
            "recommendation": "Reorder urgently" if p.quantity == 0 else "Reorder soon",
        })

    return {
        "currency": "SLL",
        "at_risk_products": at_risk,
        "total_at_risk": len(at_risk),
    }
