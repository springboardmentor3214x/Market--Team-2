import os
from typing import List
from dotenv import load_dotenv

# Safely target project .env only
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    try:
        load_dotenv(dotenv_path=env_path)
    except Exception:
        pass

class Settings:
    PROJECT_NAME: str = "Market Research AI"
    API_V1_STR: str = "/api/v1"
    
    # JWT Settings
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "market-research-secret-key-32bytes-long-super-secure!"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    
    # Database Settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./stock_research_db.sqlite"
    )

    # Market Data API Keys
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "4QLGLRF2NM5IP9V2")
    
    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()
