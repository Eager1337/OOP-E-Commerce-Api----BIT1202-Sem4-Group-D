# E-Commerce Inventory API

A production-ready REST API for managing e-commerce inventory, built with **FastAPI** and **PostgreSQL**.
Developed for **Limkokwing University — PROG315: Object-Oriented Programming 2**, Semester 4 (March–July 2026).

**Currency**: Sierra Leonean Leone (Le / SLL)  
**SDG Alignment**: SDG 8 — Decent Work and Economic Growth  
Empowering local Sierra Leone businesses with modern digital inventory tools.

---

## Features

| Feature | Detail |
|---------|--------|
| **Products** | Full CRUD, inventory tracking, low-stock alerts, restock |
| **Categories** | Organise products with slugs and descriptions |
| **Suppliers** | Manage Sierra Leone product suppliers (city/country defaults to Freetown/SL) |
| **Orders** | Auto stock deduction, coupon support, Sierra Leonean Leone totals |
| **Coupons & Discounts** | Percentage or fixed-Le discount codes with expiry and usage limits |
| **Product Reviews** | Star ratings (1–5) and customer feedback, one review per user per product |
| **Analytics** | Revenue summary, top products, profit margins, low-revenue risk report |
| **Authentication** | OAuth2 + JWT Bearer tokens |
| **Authorization** | Role-based access: Admin / Manager / Viewer |
| **Documentation** | Auto-generated Swagger UI (`/docs`) and ReDoc (`/redoc`) |
| **Async Support** | `async/await` for I/O-bound operations |
| **Dependency Injection** | FastAPI `Depends()` for DB sessions and auth throughout |

---

## Tech Stack

- **Framework**: FastAPI 0.115
- **Database**: PostgreSQL + SQLAlchemy 2.0 ORM
- **Auth**: OAuth2 password flow + JWT (PyJWT) + bcrypt (passlib)
- **Validation**: Pydantic v2 with type annotations
- **Docs**: Swagger UI (`/docs`) and ReDoc (`/redoc`)
- **Currency**: Sierra Leonean Leone (Le / SLL)
- **License**: MIT

---

## Project Structure

```
ecommerce_api/
├── app/
│   ├── main.py              # FastAPI app entry point — registers all routers
│   ├── database.py          # SQLAlchemy engine + get_db() DI
│   ├── models.py            # ORM models: User, Product, Category, Order,
│   │                        #             Supplier, Coupon, ProductReview
│   ├── schemas.py           # Pydantic request/response schemas (SLL currency)
│   ├── auth.py              # JWT creation/validation, RBAC dependencies
│   └── routers/
│       ├── auth.py          # POST /auth/register, /auth/login, /auth/me
│       ├── users.py         # Admin-only user management
│       ├── categories.py    # Category CRUD
│       ├── products.py      # Product CRUD + inventory alerts + stats
│       ├── orders.py        # Order management with stock deduction + coupons
│       ├── suppliers.py     # Supplier management (Sierra Leone businesses)
│       ├── coupons.py       # Discount codes — percentage or fixed Le
│       ├── reviews.py       # Product star ratings and comments
│       └── analytics.py    # Revenue reports, profit margins, risk alerts
├── .env.example             # Copy to .env with your local DB details
├── requirements.txt
└── README.md
```

---

## Running Locally — VS Code (Step by Step)

### What you need installed

| Tool | Download |
|------|----------|
| Python 3.9+ | https://www.python.org/downloads/ |
| PostgreSQL 13+ | https://www.postgresql.org/download/ |
| VS Code | https://code.visualstudio.com/ |
| VS Code Python extension | Search "Python" by Microsoft in Extensions |

---

### Step 1 — Open the project in VS Code

Open the `ecommerce_api/` folder in VS Code.

---

### Step 2 — Create a virtual environment

Open the VS Code Terminal (`Ctrl + backtick`) and run:

```bash
# Windows
python -m venv venv
venv\Scripts\activate


# Mac / Linux
python -m venv venv
source venv/bin/activate
```

You will see `(venv)` appear in your terminal prompt.

---

### Step 3 — Install all dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, SQLAlchemy, PyJWT, passlib, psycopg2, and all other required packages.

---

### Step 4 — Create your .env file

Create a file named `.env` inside the `ecommerce_api/` folder with this content:

```env
DATABASE_URL=postgresql://postgres:12345678@localhost:5432/ecommerce_db
SECRET_KEY=limkokwing-ecommerce-secret-key-prog315-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> Your `ecommerce_db` database is already created in pgAdmin, so this will connect straight away.

---

### Step 5 — Run the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

The API automatically creates all database tables on first run.

---

### Step 6 — Open Swagger UI

Go to: **http://localhost:8000/docs**

You will see the full interactive API documentation with all endpoints.

---

### Optional — Run with F5 (VS Code debugger)

A `.vscode/launch.json` file is included. Just press **F5** to start the server inside VS Code with debugging enabled.

---

## API Endpoints

### Authentication (no token needed)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login — returns JWT token |
| `GET` | `/api/v1/auth/me` | Get current user info |

### Users (Admin only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/users/` | List all users |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `PUT` | `/api/v1/users/{id}` | Update user |
| `DELETE` | `/api/v1/users/{id}` | Delete user |

### Categories

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/categories/` | Any | List all categories |
| `POST` | `/api/v1/categories/` | Manager/Admin | Create category |
| `PUT` | `/api/v1/categories/{id}` | Manager/Admin | Update category |
| `DELETE` | `/api/v1/categories/{id}` | Manager/Admin | Delete category |

### Products

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/products/` | Any | List products (search, price, category filters) |
| `GET` | `/api/v1/products/{id}` | Any | Get product (shows SLL price + currency) |
| `POST` | `/api/v1/products/` | Manager/Admin | Create product |
| `PUT` | `/api/v1/products/{id}` | Manager/Admin | Update product |
| `DELETE` | `/api/v1/products/{id}` | Manager/Admin | Delete product |
| `GET` | `/api/v1/products/inventory/alerts` | Manager/Admin | **Low stock alerts** |
| `POST` | `/api/v1/products/{id}/restock` | Manager/Admin | Add stock |
| `GET` | `/api/v1/products/stats/overview` | Manager/Admin | Inventory stats |

### Orders (prices in Le)

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/orders/` | Any | List orders (viewers see own only) |
| `GET` | `/api/v1/orders/{id}` | Any | Get order details |
| `POST` | `/api/v1/orders/` | Any | **Create order** (auto deducts stock, supports coupon) |
| `PUT` | `/api/v1/orders/{id}` | Manager/Admin | Update order status |
| `DELETE` | `/api/v1/orders/{id}` | Manager/Admin | Cancel order (restores stock) |

### Suppliers

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/suppliers/` | Any | List suppliers |
| `GET` | `/api/v1/suppliers/{id}` | Any | Get supplier |
| `POST` | `/api/v1/suppliers/` | Manager/Admin | Create supplier |
| `PUT` | `/api/v1/suppliers/{id}` | Manager/Admin | Update supplier |
| `DELETE` | `/api/v1/suppliers/{id}` | Manager/Admin | Deactivate supplier |

### Coupons & Discounts (Admin only to create)

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/coupons/` | Manager/Admin | List all coupons |
| `POST` | `/api/v1/coupons/` | Admin | Create discount coupon |
| `GET` | `/api/v1/coupons/validate/{code}` | Any | Validate a coupon code |
| `PUT` | `/api/v1/coupons/{id}` | Admin | Update coupon |
| `DELETE` | `/api/v1/coupons/{id}` | Admin | Deactivate coupon |

### Product Reviews

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/reviews/product/{id}` | Any | Get reviews for a product |
| `GET` | `/api/v1/reviews/product/{id}/summary` | Any | Star rating summary |
| `POST` | `/api/v1/reviews/product/{id}` | Any | Submit a review (1–5 stars) |
| `DELETE` | `/api/v1/reviews/{id}` | Any/Admin | Delete review |

### Analytics & Reports

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/analytics/summary` | Manager/Admin | Revenue summary (daily/top products/by category) |
| `GET` | `/api/v1/analytics/profit-margins` | Manager/Admin | Profit margin per product |
| `GET` | `/api/v1/analytics/low-revenue-risk` | Manager/Admin | Products at risk of zero revenue |

---

## Role-Based Access Control

| Role | Access |
|------|--------|
| **Admin** | Full access — users, coupons, all data |
| **Manager** | Products, categories, orders, suppliers, analytics |
| **Viewer** | Read products/categories; own orders; write reviews |

---

## Complete Demo Flow (copy-paste ready)

### 1. Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","username":"admin","password":"Admin1234!","full_name":"Admin User","role":"admin"}'
```

### 2. Login — copy your token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin1234!"
```

Set your token: `TOKEN=<paste your access_token here>`

### 3. Create a supplier

```bash
curl -X POST http://localhost:8000/api/v1/suppliers/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Freetown Electronics Ltd","contact_person":"Mohamed Bangura","phone":"+232 76 123456","city":"Freetown","country":"Sierra Leone"}'
```

### 4. Create a category

```bash
curl -X POST http://localhost:8000/api/v1/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Electronics","description":"Electronic devices","slug":"electronics"}'
```

### 5. Create a product (price in Le)

```bash
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Wireless Headphones","sku":"WH-001","price":950000,"cost_price":600000,"quantity":5,"reorder_level":10,"category_id":1,"supplier_id":1}'
```

### 6. Check low-stock alerts

```bash
curl http://localhost:8000/api/v1/products/inventory/alerts \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
[{"product_id":1,"product_name":"Wireless Headphones","current_quantity":5,"reorder_level":10,"status":"low_stock"}]
```

### 7. Create a discount coupon

```bash
curl -X POST http://localhost:8000/api/v1/coupons/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"FREETOWN20","description":"20% off for Freetown customers","discount_type":"percentage","discount_value":20,"min_order_amount":500000}'
```

### 8. Place an order with coupon

```bash
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"product_id":1,"quantity":1}],"shipping_address":"15 Wilberforce Street, Freetown, Sierra Leone","coupon_code":"FREETOWN20","notes":"Demo order"}'
```

Response shows:
```json
{
  "order_number": "ORD-EE07A35E",
  "total_amount": 760000,
  "discount_amount": 190000,
  "currency": "SLL",
  "currency_symbol": "Le"
}
```

### 9. Submit a product review

```bash
curl -X POST http://localhost:8000/api/v1/reviews/product/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating":5,"comment":"Excellent product, great value for Sierra Leone!"}'
```

### 10. View analytics

```bash
curl "http://localhost:8000/api/v1/analytics/summary?days=30" \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:8000/api/v1/analytics/profit-margins \
  -H "Authorization: Bearer $TOKEN"
```

---

## Dependency Injection (PROG315 Key Concept)

FastAPI's `Depends()` is used throughout for clean, testable code:

```python
# database.py — yields a DB session, always closes it after use
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# auth.py — verifies JWT and returns the current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    ...

# Reusable role guards
require_admin = require_role([UserRole.admin])
require_manager_or_admin = require_role([UserRole.admin, UserRole.manager])

# Any route — inject DB + auth in one line
@router.get("/products/")
async def list_products(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    ...
```

---

## Security Implementation

| Requirement | Implementation |
|-------------|----------------|
| Password hashing | `passlib` with `bcrypt` — never stores plain text |
| Stateless auth | JWT tokens (`PyJWT`, HS256 algorithm) |
| Token expiry | Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Role enforcement | `require_admin`, `require_manager_or_admin` as DI dependencies |
| CORS | FastAPI `CORSMiddleware` |

---

## SDG 8 — Decent Work and Economic Growth

This API directly supports SDG 8 in Sierra Leone by:

| Impact | How |
|--------|-----|
| **Digitise inventory** | Removes manual stock tracking errors for small businesses |
| **Reduce waste** | Low-stock alerts prevent stockouts and over-ordering |
| **Increase revenue** | Coupon/discount system attracts and retains customers |
| **Data-driven decisions** | Analytics show top products, daily sales, profit margins |
| **Supplier management** | Keeps local Sierra Leone supplier contacts organised |
| **Customer trust** | Product reviews help buyers make informed decisions |
| **Open source** | MIT licensed — free for any Sierra Leone business or developer to use |

---

## Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| DB session lifecycle | `get_db()` generator with `try/finally` — always closes safely |
| Secure passwords | bcrypt hashing via passlib |
| Stateless authentication | JWT tokens — server stores no session state |
| Stock consistency | Atomic transaction in order creation |
| Role enforcement | Reusable `Depends()` role functions — no code duplication |
| Coupon discount logic | Separate `_apply_coupon()` helper for percentage and fixed-Le |
| Auto documentation | FastAPI generates Swagger/ReDoc from Python type annotations |

---

## License

This project is licensed under the **MIT License**.

---

## Contributors

- [Your Group Member Names Here]
- **Lecturer**: Amandus Benjamin Coker — amandus.bcoker@limkokwing.edu.sl

---

*Limkokwing University of Creative Technology — Sierra Leone*  
*PROG315 — Object-Oriented Programming 2 | Semester 4 | March–July 2026*
