from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User, UserRole
from src.schemas import UserResponse, UserUpdate
from src.auth import get_password_hash, require_admin, require_any

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse], summary="List all users")
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    role: UserRole | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    _: User = Depends(require_any),
):
    """
    List all users with optional filtering.
    Requires authentication.
    """
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_any)):
    """Get a specific user by ID. Requires authentication."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="Update user")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Update a user. Admin only.

    - Can change role, active status, email, etc.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = db.query(User).filter(User.email == update_data["email"]).first()
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")

    if "username" in update_data:
        existing = db.query(User).filter(User.username == update_data["username"]).first()
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Username already in use")

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204, summary="Delete user")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a user. Admin only. Cannot delete yourself."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
