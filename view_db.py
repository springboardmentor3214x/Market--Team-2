"""
Interactive Database Viewer
Inspect tables, row counts, and stored records for both SQLite and PostgreSQL.
Usage:
    python view_db.py
    python view_db.py users
    python view_db.py companies
    python view_db.py stock_prices
    python view_db.py research_history
    python view_db.py watchlists
"""

import sys
import json
from sqlalchemy import inspect, text
from database import engine

def inspect_database(target_table=None):
    inspector = inspect(engine)
    tables = [t for t in inspector.get_table_names() if not t.startswith("sqlite_")]

    print("=" * 70)
    print("📊 MARKET RESEARCH AI - DATABASE INSPECTION")
    print(f"🔗 Database URL: {engine.url}")
    print("=" * 70)

    if not tables:
        print("⚠️ No tables found in the database. Run 'python init_db.py' first.")
        return

    # 1. Print Summary of Tables and Counts
    print("\n📋 TABLE SUMMARY:")
    with engine.connect() as conn:
        for table in tables:
            try:
                count_res = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
                print(f"  • {table:<22} : {count_res:>5} records")
            except Exception as e:
                print(f"  • {table:<22} : (Error reading: {e})")

    # 2. Detailed View of Target Table or All Tables
    tables_to_show = [target_table] if target_table and target_table in tables else tables

    print("\n" + "=" * 70)
    print("🔍 DATA PREVIEW")
    print("=" * 70)

    with engine.connect() as conn:
        for table in tables_to_show:
            print(f"\n📦 TABLE: {table.upper()}")
            print("-" * 50)
            
            try:
                # Fetch up to 5 rows
                result = conn.execute(text(f'SELECT * FROM "{table}" LIMIT 5'))
                rows = result.fetchall()
                cols = list(result.keys())

                if not rows:
                    print("   (Empty table - no records yet)")
                    continue

                for i, row in enumerate(rows, 1):
                    row_dict = dict(zip(cols, row))
                    # Sanitize password hash for display
                    if "password_hash" in row_dict:
                        row_dict["password_hash"] = row_dict["password_hash"][:15] + "..."
                    
                    # Pretty print JSON fields
                    for k, v in row_dict.items():
                        if isinstance(v, (dict, list)):
                            row_dict[k] = json.dumps(v)

                    print(f"  Record #{i}:")
                    for col_name in cols:
                        val = row_dict.get(col_name)
                        print(f"    - {col_name:<20}: {val}")
                    print()
            except Exception as e:
                print(f"   Error reading data: {e}")

if __name__ == "__main__":
    table_arg = sys.argv[1].lower() if len(sys.argv) > 1 else None
    inspect_database(table_arg)
