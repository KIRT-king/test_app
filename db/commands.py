from datetime import datetime

from fedora_third_party.cli import query
from sqlalchemy.future import select

from db.database import engine, Base, AsyncSession
from db.models import User

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_user(username: str, name: str, lastname: str, post: str, email: str, phone_number: str):
    async with AsyncSession() as session:
        try:
            new_user = User(username = username, name = name, lastname = lastname, post = post, email = email, phone_number = phone_number, status = "reg", last_check = datetime.utcnow())
            session.add(new_user)
            await session.commit()
            print("User successfully")
        except Exception as e:
            await session.rollback()
            print(e)

async def get_user(user_name: str):
    async with AsyncSession() as session:
        try:
            query = select(User).where(user_name == User.username)
            result = await session.execute(query)
            user = result.scalars().first()
            return user
        except Exception as e:
            await session.rollback()
            print(e)

async def delete_user(user_name: str):
    async with AsyncSession() as session:
        try:
            query = select(User).where(user_name == User.username)
            result = await session.execute(query)
            user = result.scalars().first()
            await session.delete(user)
            await session.commit()
            print("User deleted")
        except Exception as e:
            await session.rollback()
            print(e)

async def update_user_last_enter(user_name: str):
    async with AsyncSession() as session:
        try:
            query = select(User).where(user_name == User.username)
            result = await session.execute(query)
            user = result.scalars().first()
            if user:
                user.last_check = datetime.utcnow()
                await session.commit()
                print(f"last check changed to {datetime.utcnow()}")
            else:
                print(f"user - {user_name} not found")
        except Exception as e:
            await session.rollback()
            print(e)