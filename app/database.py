import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from decouple import config


class Base(DeclarativeBase):
    pass


engine = create_engine(
    f"postgresql+psycopg2://{config('PG_USER')}:{config('PG_PASSWORD')}@{config('PG_ADDRESS')}:{config('PG_PORT')}/{config('PG_DB')}"
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
