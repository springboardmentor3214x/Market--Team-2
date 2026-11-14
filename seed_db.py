from sqlalchemy import inspect
from database import SessionLocal, engine
import crud

def seed_and_verify():
    db = SessionLocal()
    try:
        print("🌱 Seeding test data into PostgreSQL...")

        # 1. Create User A (or fetch if already seeded)
        user_a_email = "user_a@stockresearch.com"
        user_a = crud.get_user_by_email(db, user_a_email)
        if not user_a:
            user_a = crud.create_user(
                db=db,
                email=user_a_email,
                password_hash="$2b$12$DummyBcryptHashForUserA1234567890",
                preferences={"preferred_market": "NSE", "analysis_period": "1Y"}
            )
            # User A Watchlist (Reliance, TCS, HDFC Bank)
            crud.add_to_watchlist(db, user_a.user_id, "RELIANCE.NS", "Reliance Industries", "NSE")
            crud.add_to_watchlist(db, user_a.user_id, "TCS.NS", "Tata Consultancy Services", "NSE")
            crud.add_to_watchlist(db, user_a.user_id, "HDFCBANK.NS", "HDFC Bank", "NSE")

            # User A Research History (Reliance Industries, then Tata Motors)
            crud.log_research_activity(db, user_a.user_id, "RELIANCE.NS", "Reliance Industries", "1Y")
            crud.log_research_activity(db, user_a.user_id, "TATAMOTORS.NS", "Tata Motors", "5Y")

        # 2. Create User B (or fetch if already seeded)
        user_b_email = "user_b@stockresearch.com"
        user_b = crud.get_user_by_email(db, user_b_email)
        if not user_b:
            user_b = crud.create_user(
                db=db,
                email=user_b_email,
                password_hash="$2b$12$DummyBcryptHashForUserB0987654321",
                preferences={"preferred_market": "NYSE", "analysis_period": "3Y"}
            )
            # User B Watchlist (Infosys)
            crud.add_to_watchlist(db, user_b.user_id, "INFY.NS", "Infosys", "NSE")

            # User B Research History (Infosys)
            crud.log_research_activity(db, user_b.user_id, "INFY.NS", "Infosys", "3Y")

        print(f"✅ User A created: {user_a.email} | Prefs: {user_a.preferences}")
        print(f"✅ User B created: {user_b.email} | Prefs: {user_b.preferences}\n")

        # 3. Verify Workspace Isolation
        a_history = [h.ticker_symbol for h in crud.get_user_research_history(db, user_a.user_id)]
        b_history = [h.ticker_symbol for h in crud.get_user_research_history(db, user_b.user_id)]

        a_watchlist = [w.ticker_symbol for w in crud.get_user_watchlist(db, user_a.user_id)]
        b_watchlist = [w.ticker_symbol for w in crud.get_user_watchlist(db, user_b.user_id)]

        print("🔒 WORKSPACE ISOLATION TEST:")
        print(f"   User A Watchlist:        {a_watchlist}")
        print(f"   User A Research History: {a_history}")
        print(f"   User B Watchlist:        {b_watchlist}")
        print(f"   User B Research History: {b_history}\n")

        # 4. Verify Database Indexes
        inspector = inspect(engine)
        for table in ["users", "watchlists", "research_history"]:
            indexes = [idx["name"] for idx in inspector.get_indexes(table)]
            print(f"⚡ Indexes on '{table}': {indexes}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_and_verify()