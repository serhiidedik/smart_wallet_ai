import asyncio
from database import engine, Base
from models import TransactionModel


async def init_models():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # uncomment to cleanup db

        print("Creating tables")
        await conn.run_sync(Base.metadata.create_all)
        print("Done")


if __name__ == "__main__":
    asyncio.run(init_models())
