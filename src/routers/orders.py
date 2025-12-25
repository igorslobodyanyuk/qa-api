import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models import User, Order, Product, OrderStatus, UserRole
from src.schemas import OrderCreate, OrderUpdate, OrderResponse
from src.auth import get_current_user, require_tester

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[OrderResponse], summary="List orders")
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = Query(None),
    user_id: int | None = Query(None, description="Filter by user (admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List orders.
    - Admin/tester: can see all orders, filter by user_id
    - Viewer: sees only their own orders
    """
    query = db.query(Order).options(joinedload(Order.products))

    if current_user.role == UserRole.viewer:
        query = query.filter(Order.user_id == current_user.id)
    elif user_id:
        query = query.filter(Order.user_id == user_id)

    if status:
        query = query.filter(Order.status == status)

    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=OrderResponse, status_code=201, summary="Create order")
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tester),
):
    """
    Create a new order for the current user.
    Requires tester or admin role.
    """
    products = db.query(Product).filter(Product.id.in_(data.product_ids)).all()

    if len(products) != len(data.product_ids):
        found_ids = {p.id for p in products}
        missing = set(data.product_ids) - found_ids
        raise HTTPException(status_code=400, detail=f"Products not found: {missing}")

    inactive = [p.id for p in products if not p.is_active]
    if inactive:
        raise HTTPException(status_code=400, detail=f"Products inactive: {inactive}")

    total = sum(p.price for p in products)
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    order = Order(
        order_number=order_number,
        user_id=current_user.id,
        total_amount=total,
        shipping_address=data.shipping_address,
        notes=data.notes,
    )
    order.products = products
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get an order by ID. Users can only see their own orders unless admin/tester."""
    order = (
        db.query(Order).options(joinedload(Order.products)).filter(Order.id == order_id).first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.viewer and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access other users' orders")

    return order


@router.put("/{order_id}", response_model=OrderResponse, summary="Update order")
def update_order(
    order_id: int,
    data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tester),
):
    """
    Update an order (status, shipping address, notes).
    Requires tester or admin role.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=204, summary="Delete order")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_tester),
):
    """Delete an order. Requires tester or admin role."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()


@router.post("/{order_id}/cancel", response_model=OrderResponse, summary="Cancel order")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an order. Users can cancel their own pending orders."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.viewer and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot cancel other users' orders")

    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")

    order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return order
