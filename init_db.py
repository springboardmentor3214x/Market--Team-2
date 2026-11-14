from sqlalchemy import inspect
from database import engine, Base
import models  # Imports User, Watchlist, and ResearchHistory

def create_tables():
    print("⏳ Creating tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("✅ Tables currently in stock_research_db:", tables)

    for table_name in ["users", "watchlists", "research_history"]:
        if table_name in tables:
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            fks = [fk["referred_table"] for fk in inspector.get_foreign_keys(table_name)]
            print(f"📋 '{table_name}' columns: {columns} | Linked to: {fks}")

if __name__ == "__main__":
    create_tables()