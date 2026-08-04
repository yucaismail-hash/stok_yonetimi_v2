# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(
    DATABASE_URL,
    pool_size=8,
    max_overflow=16,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"connect_timeout": 10, "sslmode": "require"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """
    Veritabanı tablolarını oluşturur.
    Migration'lar admin endpoint'leri ile yapılır.
    """
    from app import models
    
    logger.info("📌 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("🎉 Database tables created successfully!")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()