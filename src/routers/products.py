from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models import User, Product, Category
from src.schemas import ProductCreate, ProductUpdate, ProductResponse
from src.auth import require_tester, require_any

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse], summary="List all products")
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    category_id: int | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    in_stock: bool | None = Query(None, description="Filter products with stock > 0"),
    search: str | None = Query(None, description="Search by name or SKU"),
    sort_by: str | None = Query(None, enum=["price", "name", "created_at", "stock"]),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    db: Session = Depends(get_db),
    _: User = Depends(require_any),
):
    """
    List products with comprehensive filtering and sorting.

    Great for testing:
    - Pagination (skip/limit)
    - Range filters (min_price/max_price)
    - Boolean filters (is_active, in_stock)
    - Text search (search)
    - Sorting (sort_by, sort_order)
    """
    query = db.query(Product).options(joinedload(Product.category))

    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock is not None:
        if in_stock:
            query = query.filter(Product.stock > 0)
        else:
            query = query.filter(Product.stock == 0)
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) | (Product.sku.ilike(f"%{search}%"))
        )

    if sort_by:
        column = getattr(Product, sort_by, None)
        if column:
            query = query.order_by(column.desc() if sort_order == "desc" else column.asc())

    return query.offset(skip).limit(limit).all()


@router.post("", response_model=ProductResponse, status_code=201, summary="Create product")
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tester),
):
    """Create a new product. Requires tester or admin role."""
    if db.query(Product).filter(Product.sku == data.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")

    if data.category_id:
        if not db.query(Category).filter(Category.id == data.category_id).first():
            raise HTTPException(status_code=400, detail="Category not found")

    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_any),
):
    """Get a product by ID."""
    product = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse, summary="Update product")
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tester),
):
    """Update a product. Requires tester or admin role."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)

    if "sku" in update_data:
        existing = db.query(Product).filter(Product.sku == update_data["sku"]).first()
        if existing and existing.id != product_id:
            raise HTTPException(status_code=400, detail="SKU already exists")

    if "category_id" in update_data and update_data["category_id"]:
        if not db.query(Category).filter(Category.id == update_data["category_id"]).first():
            raise HTTPException(status_code=400, detail="Category not found")

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204, summary="Delete product")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_tester),
):
    """Delete a product. Will also remove from any orders."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
