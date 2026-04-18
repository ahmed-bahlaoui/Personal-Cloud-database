from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.settings import DATABASE_URL, SQL_ECHO


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=SQL_ECHO)

SessionLocal = sessionmaker(bind=engine)
