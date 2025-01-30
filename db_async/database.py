import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
DATABASE_URL = os.getenv("DATABASE_URL_ASYNC")


engine = create_async_engine(DATABASE_URL, echo = True)
Base = declarative_base()
AsyncSession = async_sessionmaker(bind=engine, expire_on_commit=False)