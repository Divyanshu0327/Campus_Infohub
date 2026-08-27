from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Update these with your actual database credentials
# User: root, Password: (empty), Host: localhost, DB: college_hub
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Absolute path ensures consistent DB file whether running from root or backend directory
DB_PATH = os.path.join(BASE_DIR, "college_hub.db")
if not os.path.exists(DB_PATH):
    parent_db = os.path.join(BASE_DIR, "..", "college_hub.db")
    if os.path.exists(parent_db):
        DB_PATH = parent_db

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.abspath(DB_PATH)}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
