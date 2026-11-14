import os
from sqlalchemy import text
from backend.app.db.session import engine, SessionLocal, Base, get_db, GUID, JSONType
from backend.app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

__all__ = ["engine", "SessionLocal", "Base", "get_db", "DATABASE_URL", "GUID", "JSONType"]

if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1;"))
            print("✅ Successfully connected to database!")
    except Exception as e:
        print("❌ Connection failed:", e)
