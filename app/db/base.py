"""
Database engine, session factory, and declarative base.

Reads DATABASE_URL from the environment.
Supabase connection strings look like:
  postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
Add ?sslmode=require to the URL in your .env if Supabase requires SSL.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
