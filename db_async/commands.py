from datetime import datetime, timedelta
from sqlalchemy.future import select

from db_async.database import engine, Base, AsyncSession
from db_async.models import User

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_user(username: str, name: str, lastname: str, post: str, email: str, phone_number: str):
    async with AsyncSession() as session:
        try:
            new_user = User(username = username, name = name, lastname = lastname, post = post, email = email, phone_number = phone_number, status = "reg", last_check = "-")
            session.add(new_user)
            await session.commit()
            print("User successfully")
            return True
        except Exception as e:
            await session.rollback()
            print(e)
            return False

async def get_user(user_name: str):
    async with AsyncSession() as session:
        try:
            query = select(User).where(User.username == user_name)
            result = await session.execute(query)
            user = result.scalars().first()
            return user
        except Exception as e:
            await session.rollback()
            print(e)

async def delete_user(user_name: str):
    async with AsyncSession() as session:
        try:
            query = select(User).where(User.username == user_name)
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
            query = select(User).where(User.username == user_name)
            result = await session.execute(query)
            user = result.scalars().first()
            if user:
                utc_now = datetime.utcnow()
                moscow_time = utc_now + timedelta(hours=3)
                formatted_time = moscow_time.strftime("%H:%M %d:%m:%Y")

                user.last_check = formatted_time
                await session.commit()
                print(f"last check changed to {formatted_time}")
            else:
                print(f"user - {user_name} not found")
        except Exception as e:
            await session.rollback()
            print(e)

async def check_user_exist(user_name: str, user_email: str):
    async with AsyncSession() as session_check:
        try:
            query_username = select(User).where(User.username == user_name)
            result_username = await session_check.execute(query_username)
            username_exists = result_username.scalars().first() is not None

            query_email = select(User).where(User.email == user_email)
            result_email = await session_check.execute(query_email)
            email_exists = result_email.scalars().first() is not None

            return username_exists, email_exists
        except Exception as e:
            print(e)
            return False, False

