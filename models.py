from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="UAH")
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    merchant = Column(String, nullable=True)

    # created_at аналог
    created_at = Column(DateTime(timezone=True), server_default=func.now())