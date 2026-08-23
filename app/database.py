import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass

if "data" not in os.listdir(os.getcwd()):
    os.mkdir("data")

engine = create_engine("sqlite:///data/app.db")
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
