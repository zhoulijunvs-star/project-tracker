"""
Project Tracker - Database Session Management
"""

from contextlib import contextmanager
from sqlalchemy.orm import Session, sessionmaker
from models import init_db

engine = init_db()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session():
    """Context manager for non-FastAPI contexts"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
