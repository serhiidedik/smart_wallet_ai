import os
import shutil
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# locally imports
from database import get_db
from models import TransactionModel
from parser import parse_expense, parse_receipt_image
from schemas import Transaction as TransactionSchema

app = FastAPI(title="SmartWallet AI")


# user input
class TransactionRequest(BaseModel):
    text: str


async def save_transaction_to_db(data: TransactionSchema, db: AsyncSession):
    # Map Pydantic schema to SQLAlchemy model
    db_transaction = TransactionModel(
        amount=data.amount,
        currency=data.currency,
        category=data.category.value,
        description=data.description,
        merchant=data.merchant
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction


# endpoints

@app.post("/transactions/text", response_model=TransactionSchema)
async def create_transaction_text(
        request: TransactionRequest,
        db: AsyncSession = Depends(get_db)
):
    print(f"📩 Text received: {request.text}")

    try:
        # Run blocking sync function in a separate thread
        parsed_data = await run_in_threadpool(parse_expense, request.text)
        print(f"🤖 AI Result: {parsed_data}")

        await save_transaction_to_db(parsed_data, db)
        return parsed_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")


@app.post("/transactions/image", response_model=TransactionSchema)
async def create_transaction_image(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    print(f"📩 Image received: {file.filename}")

    # Save uploaded file temporarily because parser needs a path
    temp_filename = f"temp_{file.filename}"

    try:
        # Write file to disk
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run vision model in threadpool to avoid blocking event loop
        parsed_data = await run_in_threadpool(parse_receipt_image, temp_filename)
        print(f"🤖 Vision Result: {parsed_data}")

        await save_transaction_to_db(parsed_data, db)
        return parsed_data

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Vision Error: {str(e)}")

    finally:
        # Cleanup: remove temp file even if error occurred
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@app.get("/transactions/")
async def get_transactions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TransactionModel).order_by(TransactionModel.id.desc()))
    return result.scalars().all()