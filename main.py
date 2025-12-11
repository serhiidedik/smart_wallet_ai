from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# locally imports
from database import get_db
from models import TransactionModel
from parser import parse_expense
from schemas import Transaction as TransactionSchema

app = FastAPI(title="SmartWallet AI")


# user input
class TransactionRequest(BaseModel):
    text: str


# create transaction
@app.post("/transactions/", response_model=TransactionSchema)
async def create_transaction(
        request: TransactionRequest,
        db: AsyncSession = Depends(get_db)  # Dependency Injection сессии БД
):
    print(f"📩 Request text: {request.text}")

    try:
        # NOTE: parse_expense should be replaced with async
        parsed_data = parse_expense(request.text)
        print(f"🤖 Parsed data: {parsed_data}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
    # save into DB
    db_transaction = TransactionModel(
        amount=parsed_data.amount,
        currency=parsed_data.currency,
        category=parsed_data.category.value,
        description=parsed_data.description,
        merchant=parsed_data.merchant
    )

    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)

    return parsed_data


# 3. read transactions
@app.get("/transactions/")
async def get_transactions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransactionModel).order_by(TransactionModel.id.desc()))
    transactions = result.scalars().all()
    return transactions