from sqlalchemy import Column, Integer, String, TIMESTAMP

from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    post = Column(String(150))
    email = Column(String(255), nullable=False, unique=True)
    phone_number = Column(String(20))
    status = Column(String(100), nullable=False)
    last_check = Column(String(50), nullable=False)

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, name={self.name})"