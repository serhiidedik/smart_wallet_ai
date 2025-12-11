import os
import shutil
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import TransactionModel
from parser import parse_expense, parse_receipt_image
from schemas import Transaction as TransactionSchema

app = FastAPI(title="SmartWallet AI")


class TextRequest(BaseModel):
    text: str


# --- 1. Pure Analysis Endpoints (No DB Save) ---

@app.post("/analyze/text", response_model=TransactionSchema)
async def analyze_text(request: TextRequest):
    """
    Step 1: AI processes text and returns suggested structure.
    Does NOT save to DB.
    """
    print(f"🧠 Analyzing text: {request.text}")
    try:
        # Run sync parser in threadpool
        parsed_data = await run_in_threadpool(parse_expense, request.text)
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")


@app.post("/analyze/image", response_model=TransactionSchema)
async def analyze_image(file: UploadFile = File(...)):
    """
    Step 1: AI processes image and returns suggested structure.
    Does NOT save to DB.
    """
    print(f"🧠 Analyzing image: {file.filename}")
    temp_filename = f"temp_{file.filename}"

    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        parsed_data = await run_in_threadpool(parse_receipt_image, temp_filename)
        return parsed_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision Error: {str(e)}")

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


# --- 2. Database Action Endpoints ---

@app.post("/transactions/", response_model=TransactionSchema)
async def save_transaction(
        transaction_data: TransactionSchema,  # Receives final validated JSON
        db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Save the (potentially edited) data to Postgres.
    """
    print(f"💾 Saving to DB: {transaction_data}")

    db_transaction = TransactionModel(
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        category=transaction_data.category.value,
        description=transaction_data.description,
        merchant=transaction_data.merchant
    )

    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)

    return transaction_data  # Return saved data


@app.get("/transactions/")
async def get_transactions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransactionModel).order_by(TransactionModel.id.desc()))
    return result.scalars().all()