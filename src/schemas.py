from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from src.models import UserRole, OrderStatus


# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
    role: UserRole | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    role: UserRole = UserRole.tester


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


# Product schemas
class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    sku: str = Field(min_length=1, max_length=50)
    category_id: int | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    category_id: int | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse | None = None


# Order schemas
class OrderBase(BaseModel):
    shipping_address: str | None = None
    notes: str | None = None


class OrderCreate(OrderBase):
    product_ids: list[int] = Field(min_length=1)


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    shipping_address: str | None = None
    notes: str | None = None


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    user_id: int
    status: OrderStatus
    total_amount: float
    created_at: datetime
    updated_at: datetime
    products: list[ProductResponse] = []


# Pagination
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int


# Admin
class ResetResponse(BaseModel):
    message: str
    users_created: int
    categories_created: int
    products_created: int
    orders_created: int
