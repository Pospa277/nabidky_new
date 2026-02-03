"""Konfigurace databáze."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'database.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency pro získání databázové session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Vytvoření tabulek v databázi."""
    from app.models import Product, PriceTier, Quote, QuoteItem  # noqa: F401
    Base.metadata.create_all(bind=engine)
