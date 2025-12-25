from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User, Category
from src.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from src.auth import require_tester, require_any

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryResponse], summary="List all categories")
def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    search: str | None = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    _: User = Depends(require_any),
):
    """List all categories with optional filters."""
    query = db.query(Category)

    if is_active is not None:
        query = query.filter(Category.is_active == is_active)
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))

    return query.offset(skip).limit(limit).all()


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
    summary="Create category",
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tester),
):
    """Create a new category. Requires tester or admin role."""
    if db.query(Category).filter(Category.name == data.name).first():
        raise HTTPException(status_code=400, detail="Category name already exists")

    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryResponse, summary="Get category")
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_any),
):
    """Get a category by ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryResponse, summary="Update category")
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tester),
):
    """Update a category. Requires tester or admin role."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = db.query(Category).filter(Category.name == update_data["name"]).first()
        if existing and existing.id != category_id:
            raise HTTPException(status_code=400, detail="Category name already exists")

    for key, value in update_data.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204, summary="Delete category")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_tester),
):
    """Delete a category. Products in this category will have category_id set to null."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
