import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Load variables from .env
load_dotenv()


# Get our Neon PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")


# Create the connection to PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Session = our way of talking to the database
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Base class for our database models
class Base(DeclarativeBase):
    pass