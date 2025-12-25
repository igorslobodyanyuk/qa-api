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
## QA Testing API

A complete REST API for manual QA testing with:
- **Authentication** (JWT tokens)
- **Role-based authorization** (admin, tester, viewer)
- **Full CRUD** operations
- **Relationships** between entities
- **Filtering, pagination, sorting**
- **Data reset** capability

### Test Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin (full access) |
| tester | tester123 | Tester (CRUD operations) |
| viewer | viewer123 | Viewer (read-only) |

### Quick Start

1. Login via `POST /auth/login` with username/password
2. Copy the `access_token` from response
3. Click "Authorize" button and paste the token (without "Bearer " prefix)
4. Start testing!

### Reset Data

Use `POST /admin/reset` (admin only) to restore database to initial state.
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
