from app.settings import DATABASE_URL, SQL_ECHO
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass
