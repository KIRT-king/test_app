from sqlalchemy import inspect
from sqlalchemy.future import select

from .models import User
from .database import Session, Base, engine

from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import OperationalError, SQLAlchemyError

def create_user(username: str, name: str, lastname: str, post: str, email: str, phone_number: str):
    session = Session()
    try:
        new_user = User(
            username=username,
            name=name,
            lastname=lastname,
            post=post,
            email=email,
            phone_number=phone_number,
            status="reg",
            last_check="-"
        )
        session.add(new_user)
        session.commit()
        print("User successfully created")
        return True
    except Exception as e:
        session.rollback()
        print(e)
        return False
    finally:
        session.close()

def check_user_exist(user_name: str, user_email: str):
    session = Session()
    try:
        query_username = select(User).where(User.username == user_name)
        result_username = session.execute(query_username)
        username_exists = result_username.scalars().first() is not None

        query_email = select(User).where(User.email == user_email)
        result_email = session.execute(query_email)
        email_exists = result_email.scalars().first() is not None

        return username_exists, email_exists
    except Exception as e:
        print(e)
        return False, False
    finally:
        session.close()

def test_db_connection():
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ Подключение к базе данных успешно! Таблицы: {tables}")
        return True
    except OperationalError as e:
        return False
    except SQLAlchemyError as e:
        return False

def update_user_last_enter(user_name: str):
    session = Session()
    try:
        query = select(User).where(User.username == user_name)
        result = session.execute(query)
        user = result.scalars().first()

        if user:
            moscow_tz = timezone(timedelta(hours=3))
            moscow_time = datetime.now(moscow_tz)
            user.last_check = str(moscow_time.strftime("%H:%M %d-%m-%Y"))
            session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()
