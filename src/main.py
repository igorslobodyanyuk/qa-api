from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database import engine, SessionLocal, Base
from src.models import User
from src.seed import seed_database
from src.routers import auth, users, categories, products, orders, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed if empty
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            seed_database(db)
            print("Database seeded with initial data")
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.app_name,
    description="""
A sandbox REST API designed for **manual QA testing practice**. Use this API to test
CRUD operations, authentication flows, authorization rules, validation, and error handling.

---

## Domain Model

Simple e-commerce domain with four entities:

| Entity | Description | Relationships |
|--------|-------------|---------------|
| **Users** | Test accounts with roles | Has many Orders |
| **Categories** | Product groupings | Has many Products |
| **Products** | Items with price, stock, SKU | Belongs to Category |
| **Orders** | Purchase records | Belongs to User, has many Products |

---

## Authorization Matrix

| Role | Users | Categories | Products | Orders | Admin |
|------|-------|------------|----------|--------|-------|
| **admin** | CRUD | CRUD | CRUD | CRUD (all) | Yes |
| **tester** | Read | CRUD | CRUD | CRUD (all) | No |
| **viewer** | Read | Read | Read | Read (own only) | No |

---

## Test Credentials

| Username | Password | Role | Use for testing... |
|----------|----------|------|-------------------|
| `admin` | `admin123` | Admin | Full access, data reset |
| `tester` | `tester123` | Tester | Standard CRUD workflows |
| `viewer` | `viewer123` | Viewer | Read-only, 403 scenarios |

---

## Quick Start

1. **Login**: `POST /auth/login` with `{"username":"tester","password":"tester123"}`
2. **Copy** the `access_token` from response
3. **Authorize**: Click 🔓 button above, paste token (no "Bearer" prefix needed)
4. **Test**: All endpoints now authenticated

---

## Testing Scenarios

**Happy Path**: Login → Create category → Create product → Create order → Verify

**Validation**: Missing fields, invalid email, negative price, duplicate SKU

**Authorization**: Viewer creating resources (expect 403), accessing others' orders

**Edge Cases**: Empty results, non-existent IDs (404), inactive products in orders

**Data Reset**: `POST /admin/reset` restores database to initial seeded state

---

## Seeded Data

- 3 users (admin, tester, viewer)
- 5 categories (Electronics, Clothing, Home & Garden, Books, Sports)
- 20 products with realistic prices and stock
- 10 orders in various statuses (pending, confirmed, shipped, delivered, cancelled)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - allow all for QA testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(admin.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


@app.get("/", tags=["Health"])
def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }
