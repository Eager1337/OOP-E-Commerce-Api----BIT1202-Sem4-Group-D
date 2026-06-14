"""
Pydantic schemas for request/response validation.
All monetary values are in Sierra Leonean Leone (Le / SLL).
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator  # type: ignore[import]
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, OrderStatus, DiscountType


CURRENCY = "SLL"
CURRENCY_SYMBOL = "Le"


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    email: str = Field(..., example="user@example.com")
    username: str = Field(..., example="aminata_koroma")
    full_name: Optional[str] = Field(None, example="Aminata Koroma")
    role: UserRole = Field(default=UserRole.viewer)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="SecurePass123!")


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: Optional[datetime] = None


class UserLogin(BaseModel):
    username: str = Field(..., example="aminata_koroma")
    password: str = Field(..., example="SecurePass123!")


# ==================== TOKEN SCHEMAS ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None


# ==================== CATEGORY SCHEMAS ====================

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Electronics")
    description: Optional[str] = Field(None, example="Electronic devices and accessories")
    slug: Optional[str] = Field(None, example="electronics")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None


# ==================== SUPPLIER SCHEMAS ====================

class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, example="Freetown Electronics Ltd")
    contact_person: Optional[str] = Field(None, example="Mohamed Bangura")
    email: Optional[str] = Field(None, example="supplier@freetownelectronics.sl")
    phone: Optional[str] = Field(None, example="+232 76 123456")
    address: Optional[str] = Field(None, example="15 Siaka Stevens Street")
    city: Optional[str] = Field(default="Freetown", example="Freetown")
    country: Optional[str] = Field(default="Sierra Leone", example="Sierra Leone")


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==================== PRODUCT SCHEMAS ====================

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, example="Wireless Headphones")
    description: Optional[str] = Field(None, example="High-quality wireless headphones")
    sku: str = Field(..., min_length=1, max_length=50, example="WH-001")
    price: float = Field(..., gt=0, description="Price in Sierra Leonean Leone (Le)", example=950000.0)
    cost_price: Optional[float] = Field(None, gt=0, description="Cost price in Le", example=600000.0)
    quantity: int = Field(default=0, ge=0, example=50)
    reorder_level: int = Field(default=10, ge=0, example=10)
    category_id: Optional[int] = Field(None, example=1)
    supplier_id: Optional[int] = Field(None, example=1)
    is_active: bool = Field(default=True)
    image_url: Optional[str] = Field(None, example="https://example.com/image.jpg")
    weight_kg: Optional[float] = Field(None, gt=0, example=0.3)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None
    weight_kg: Optional[float] = Field(None, gt=0)


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    currency: str = CURRENCY
    currency_symbol: str = CURRENCY_SYMBOL
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def formatted_price(self) -> str:
        return f"Le {self.price:,.0f}"


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int
    currency: str = CURRENCY


class InventoryAlert(BaseModel):
    product_id: int
    product_name: str
    current_quantity: int
    reorder_level: int
    status: str = "low_stock"


# ==================== PRODUCT REVIEW SCHEMAS ====================

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars", example=5)
    comment: Optional[str] = Field(None, max_length=1000, example="Excellent product! Works perfectly.")


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    user_id: int
    reviewer_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductRatingSummary(BaseModel):
    product_id: int
    product_name: str
    average_rating: float
    total_reviews: int
    five_star: int
    four_star: int
    three_star: int
    two_star: int
    one_star: int


# ==================== COUPON SCHEMAS ====================

class CouponBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=50, example="SAVE10")
    description: Optional[str] = Field(None, example="10% off all orders")
    discount_type: DiscountType = Field(default=DiscountType.percentage)
    discount_value: float = Field(..., gt=0, example=10.0, description="Percentage (10 = 10%) or fixed Le amount")
    min_order_amount: float = Field(default=0.0, ge=0, description="Minimum order amount in Le", example=500000.0)
    usage_limit: Optional[int] = Field(None, gt=0, description="Max uses. Leave empty for unlimited.")
    expires_at: Optional[datetime] = None


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    description: Optional[str] = None
    discount_value: Optional[float] = Field(None, gt=0)
    min_order_amount: Optional[float] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class CouponResponse(CouponBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    times_used: int
    is_active: bool
    created_at: Optional[datetime] = None


class CouponValidateResponse(BaseModel):
    valid: bool
    message: str
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    coupon_id: Optional[int] = None


# ==================== ORDER SCHEMAS ====================

class OrderItemBase(BaseModel):
    product_id: int = Field(..., example=1)
    quantity: int = Field(..., gt=0, example=2)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    unit_price: float
    subtotal: float
    product: Optional[ProductResponse] = None


class OrderBase(BaseModel):
    shipping_address: Optional[str] = Field(None, example="15 Wilberforce Street, Freetown, Sierra Leone")
    notes: Optional[str] = Field(None, example="Please call before delivery")
    coupon_code: Optional[str] = Field(None, example="SAVE10", description="Optional coupon code for discount")


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    user_id: int
    status: OrderStatus
    total_amount: float
    discount_amount: float = 0.0
    currency: str = CURRENCY
    currency_symbol: str = CURRENCY_SYMBOL
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    coupon_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []


class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int
    currency: str = CURRENCY


# ==================== ANALYTICS SCHEMAS ====================

class DailySales(BaseModel):
    date: str
    orders: int
    revenue: float
    currency: str = CURRENCY


class TopProduct(BaseModel):
    product_id: int
    product_name: str
    total_sold: int
    total_revenue: float
    currency: str = CURRENCY


class CategoryRevenue(BaseModel):
    category_id: Optional[int]
    category_name: str
    total_revenue: float
    order_count: int
    currency: str = CURRENCY


class AnalyticsSummary(BaseModel):
    period: str
    total_revenue: float
    total_orders: int
    average_order_value: float
    total_items_sold: int
    currency: str = CURRENCY
    top_products: List[TopProduct]
    daily_sales: List[DailySales]
    revenue_by_category: List[CategoryRevenue]


# ==================== HEALTH/INFO SCHEMAS ====================

class HealthCheck(BaseModel):
    status: str
    version: str
    database: str


class SDGInfo(BaseModel):
    goal_number: int
    goal_name: str
    description: str
    alignment: str
