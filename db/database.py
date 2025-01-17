import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_session
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_async_engine(DATABASE_URL, echo = True)
Base = declarative_base()

# async_session = sessionmaker(bind = engine, class_=AsyncSession, expire_on_commit=False)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


