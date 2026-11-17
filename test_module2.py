from database import SessionLocal
import market_data_service
import crud

def run_module2_verification():
    db = SessionLocal()
    try:
        print("=" * 65)
        print("🚀 MODULE 2 END-TO-END VERIFICATION: STOCK SEARCH & MARKET DATA")
        print("=" * 65)

        # 1. Test Invalid Company / Ticker Handling (Requirement 1)
        print("\n1️⃣ Testing Invalid Company Search ('INVALIDCOMPANY99999')...")
        bad_res = market_data_service.collect_and_store_stock_data(db, "INVALIDCOMPANY99999")
        print("   Result:", bad_res)

        # 2. Test Indian Market Stock by Company Name ('Infosys' -> NSE / INR)
        print("\n2️⃣ Collecting Indian Stock by Company Name ('Infosys', period='1mo', market='NSE')...")
        infy_res = market_data_service.collect_and_store_stock_data(
            db, query_or_ticker="Infosys", period="1mo", preferred_market="NSE"
        )
        if infy_res["status"] == "success":
            meta = infy_res["metadata"]
            print(f"   ✅ Company: {meta['company']} ({meta['ticker_symbol']})")
            print(f"   ✅ Market & Currency: {meta['exchange']} | {meta['currency']}")
            print(f"   ✅ Source & Timestamp: {meta['data_source']} | Retrieved At: {meta['retrieved_at']}")
            print(f"   ✅ OHLCV Stored: {infy_res['ohlcv_collection']['records_stored_in_db']} rows")
            print(f"   📋 Validation Report: {infy_res['ohlcv_collection']['validation_report']}")
            print(f"   📊 Latest Session OHLCV: {infy_res['ohlcv_collection']['latest_5_sessions'][-1]}")
            print(f"   📑 Financial Statements Stored: {infy_res['financial_statements']}")
        else:
            print("   ❌ Failed:", infy_res)

        # 3. Test US Market Stock by Ticker ('AAPL' -> NASDAQ / USD)
        print("\n3️⃣ Collecting US Stock by Ticker ('AAPL', period='1mo')...")
        aapl_res = market_data_service.collect_and_store_stock_data(
            db, query_or_ticker="AAPL", period="1mo"
        )
        if aapl_res["status"] == "success":
            meta = aapl_res["metadata"]
            print(f"   ✅ Company: {meta['company']} ({meta['ticker_symbol']})")
            print(f"   ✅ Market & Currency: {meta['exchange']} | {meta['currency']}")
            print(f"   ✅ OHLCV Stored: {aapl_res['ohlcv_collection']['records_stored_in_db']} rows")
            print(f"   📑 Financial Statements Stored: {aapl_res['financial_statements']}")
        else:
            print("   ❌ Failed:", aapl_res)

        # 4. Verify PostgreSQL Database Records Directly
        print("\n4️⃣ Verifying PostgreSQL Database Storage (trade_date vs retrieved_at)...")
        db_prices = crud.get_historical_prices(db, "INFY.NS", limit=2)
        for p in db_prices:
            print(
                f"   🗄️ DB Row -> Ticker: {p.ticker_symbol} | Trade Date: {p.trade_date} | "
                f"Close: {p.close_price} | Vol: {p.volume} | Source: {p.data_source} | "
                f"Retrieved At: {p.retrieved_at.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            )

        db_stmts = crud.get_company_financial_statements(db, "INFY.NS")
        print(f"   🗄️ Total Financial Statement periods stored in PostgreSQL for INFY.NS: {len(db_stmts)}")

    finally:
        db.close()

if __name__ == "__main__":
    run_module2_verification()