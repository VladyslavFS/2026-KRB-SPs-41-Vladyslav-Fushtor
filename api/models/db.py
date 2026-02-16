from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

SessionLocal = None


def init_db(database_url: str):
    """Initialize database engine and session factory"""
    global SessionLocal
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine