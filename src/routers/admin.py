from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User
from src.schemas import ResetResponse
from src.auth import require_admin
from src.seed import seed_database, clear_database

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/reset", response_model=ResetResponse, summary="Reset database to seed data")
def reset_database(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    **DANGER ZONE**: Clears all data and reseeds the database.

    Admin only. Use this to restore the database to a known state for testing.

    Creates:
    - 3 users (admin, tester, viewer)
    - 5 categories
    - 20 products
    - 10 orders
    """
    clear_database(db)
    stats = seed_database(db)
    return ResetResponse(message="Database reset successfully", **stats)


@router.get("/stats", summary="Get database statistics")
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Get current record counts for all tables."""
    from src.models import User, Category, Product, Order

    return {
        "users": db.query(User).count(),
        "categories": db.query(Category).count(),
        "products": db.query(Product).count(),
        "orders": db.query(Order).count(),
    }
