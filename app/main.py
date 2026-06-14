"""
E-Commerce Inventory API — Main Application
FastAPI | PostgreSQL | JWT Auth | Sierra Leonean Leone (Le)

Limkokwing University — PROG315: Object-Oriented Programming 2
Semester 4 | March–July 2026 | Sierra Leone

SDG 8: Decent Work and Economic Growth
Empowering Sierra Leone businesses with digital inventory management.

Core Features Implemented:
- FastAPI framework with full CRUD operations
- PostgreSQL + SQLAlchemy ORM with Dependency Injection
- OAuth2 + JWT Authentication & Role-Based Access Control
- RESTful API design (proper HTTP methods and status codes)
- Swagger UI (/docs) and ReDoc (/redoc) auto-documentation
- Async/await for I/O-bound operations
- Supplier Management for Sierra Leone businesses
- Coupon & Discount System (percentage and fixed Le discounts)
- Product Reviews & Star Ratings
- Sales Analytics & Profit Margin Reports
- Currency: Sierra Leonean Leone (Le / SLL)
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routers import auth, users, categories, products, orders
from app.routers import suppliers, coupons, reviews, analytics
from app.schemas import HealthCheck, SDGInfo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Creates all database tables on startup (safe to run repeatedly)."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="E-Commerce Inventory API",
    description="""
## E-Commerce Inventory Management System
**Limkokwing University — PROG315** | Sierra Leone | Semester 4 (2026)

All monetary values are in **Sierra Leonean Leone (Le / SLL)**.

---

### 🛒 Core Features
- **Products** — Full CRUD, low-stock alerts, restock, inventory stats
- **Categories** — Organise products with slugs
- **Orders** — Place orders with automatic stock deduction + coupon support
- **Suppliers** — Manage Sierra Leone product suppliers
- **Coupons** — Percentage and fixed-Le discount codes
- **Reviews** — Star ratings (1–5) and customer feedback
- **Analytics** — Revenue reports, top products, profit margins

### 🔐 Authentication
All protected endpoints require a **JWT Bearer token**.
1. Register at `POST /api/v1/auth/register`
2. Login at `POST /api/v1/auth/login` to get your token
3. Click **Authorize** above and enter: `Bearer <your_token>`

### 👥 Roles
| Role | Access |
|------|--------|
| **Admin** | Full access — users, coupons, everything |
| **Manager** | Products, categories, orders, suppliers, analytics |
| **Viewer** | Read products/categories, create and view own orders, write reviews |

### 🌍 SDG Alignment
**SDG 8 — Decent Work and Economic Growth**
Empowering local Sierra Leone businesses with modern digital inventory tools.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "Limkokwing University — PROG315",
        "email": "amandus.bcoker@limkokwing.edu.sl",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")

# Extended feature routers
app.include_router(suppliers.router, prefix="/api/v1")
app.include_router(coupons.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """API root — navigation links and quick info."""
    return {
        "message": "E-Commerce Inventory API",
        "version": "2.0.0",
        "currency": "Sierra Leonean Leone (Le / SLL)",
        "university": "Limkokwing University — PROG315",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "categories": "/api/v1/categories",
            "products": "/api/v1/products",
            "orders": "/api/v1/orders",
            "suppliers": "/api/v1/suppliers",
            "coupons": "/api/v1/coupons",
            "reviews": "/api/v1/reviews",
            "analytics": "/api/v1/analytics",
        },
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Health check — confirms API and database are running."""
    return HealthCheck(status="healthy", version="2.0.0", database="connected")


@app.get("/sdg", response_model=SDGInfo, tags=["SDG"])
async def sdg_info():
    """
    SDG 8 Alignment — Decent Work and Economic Growth.

    This API supports Sierra Leone businesses by:
    - Digitising inventory management to reduce stockouts and waste
    - Providing real-time low-stock alerts and profit margin analysis
    - Enabling coupon-based promotions to attract customers
    - Offering supplier tracking within Sierra Leone
    - Open-source MIT license for community reuse and learning
    """
    return SDGInfo(
        goal_number=8,
        goal_name="Decent Work and Economic Growth",
        description="Promote sustained, inclusive economic growth and productive employment",
        alignment=(
            "This E-Commerce Inventory API supports SDG 8 by enabling local Sierra Leone "
            "businesses to digitise inventory management, reduce waste, and improve cash flow. "
            "The coupon and discount system supports customer retention. Supplier management "
            "keeps procurement organised. Analytics help owners make data-driven decisions. "
            "The open-source MIT license promotes collaborative development and knowledge "
            "sharing within the Sierra Leone tech community."
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Consistent JSON error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "status_code": exc.status_code, "detail": exc.detail},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
