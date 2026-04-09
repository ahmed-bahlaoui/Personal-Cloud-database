from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cloud_storage"


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine)
