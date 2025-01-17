from sqlalchemy import Column, Integer, String

from db.database import Base

class Logs(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    message = Column(String, nullable=False)