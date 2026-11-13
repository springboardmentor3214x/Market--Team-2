import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Check your .env file.")

# 2. Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# 3. Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class that your database tables (models.py) will inherit from in Phase 2
Base = declarative_base()

# 5. FastAPI Dependency: yields a DB session for each request and closes it after
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- STEP 6: TEST CONNECTION ---
if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            print("✅ Successfully connected to:", result.fetchone()[0])
    except Exception as e:
        print("❌ Connection failed:", e)