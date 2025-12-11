from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# Создаем Enums (как в Rails, только строже)
class Category(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    BILLS = "bills"
    OTHER = "other"

# Это твоя Модель. Аналог ActiveModel, но только для валидации данных
class Transaction(BaseModel):
    amount: float = Field(..., description="amount")
    currency: str = Field(default="UAH", description="currency")
    category: Category = Field(..., description="category")
    description: Optional[str] = Field(None, description="short description")
    merchant: Optional[str] = Field(None, description="merchant")

