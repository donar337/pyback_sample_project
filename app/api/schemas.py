from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)
    price: Decimal = Field(gt=0)


class OrderCreate(BaseModel):
    customer_id: UUID
    items: list[OrderItemCreate]


class OrderItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    price: Decimal


class OrderResponse(BaseModel):
    order_id: UUID
    customer_id: UUID
    status: str
    total_price: Decimal
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
