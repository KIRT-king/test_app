from sqlalchemy.future import select

from .models import User
from .database import Session, Base, engine


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