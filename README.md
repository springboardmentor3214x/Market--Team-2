# Market Research AI — Multi-Agent Financial Intelligence Platform

AI-Powered Stock Research platform with specialized autonomous agents for:
- 📰 **News & Sentiment Intelligence Agent (Module 3)** (Loughran-McDonald financial tone classification, corporate events detection, conflict resolution, and source verification).
- 📊 **Fundamental Analysis Agent** (revenue, profitability, debt, financial ratios).
- 📈 **Technical Analysis Agent** (SMA, EMA, RSI, MACD, historical volatility).
- 🛡️ **Risk Analysis Agent** (drawdown, market volatility, uncertainty assessment).
- ⚡ **Automated Data Validation Pipeline** (Pandas cleaning engine, OHLC anomaly detection, duplicate removal, SQLite/PostgreSQL dual-database support).

---

## Quick Start Guide (Copy & Paste)

Open **two separate terminals** in the project directory (`Market--Team-2`).

### Terminal 1: Start Backend API (FastAPI)

```powershell
# Activate Python Virtual Environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Run Uvicorn Server
uvicorn backend.app.main:app --reload --port 8000
```

> **Or run directly in one line without activating:**
> ```powershell
> .\venv\Scripts\uvicorn.exe backend.app.main:app --reload --port 8000
> ```

- **Backend API URL:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Terminal 2: Start Frontend UI (Vite + React)

```powershell
# Start Vite Development Server
npm run dev
```

- **Frontend Application URL:** [http://localhost:5173](http://localhost:5173)

---

## First-Time Setup Instructions

### 1. Python Virtual Environment Setup (Backend)
```powershell
# 1. Create virtualenv (if not already created)
python -m venv venv

# 2. Install dependencies
.\venv\Scripts\pip.exe install -r requirements.txt

# 3. Initialize SQLite Database Schema
.\venv\Scripts\python.exe init_db.py

# 4. Stamp Alembic Database Migrations
.\venv\Scripts\alembic.exe stamp head
```

### 2. Node.js Setup (Frontend)
```powershell
# Install npm packages
npm install
```

---

## Running Automated Test Suites

Run all 27 unit and integration tests across Module 1, Module 2, and Module 3:

```powershell
.\venv\Scripts\pytest.exe -v
```

### Included Test Suites:
1. `test_module1_backend.py` — Auth, registration, JWT login, preferences, watchlist.
2. `test_module2_stocks.py` — Alpha Vantage & yfinance data retrieval, Pandas cleaning pipeline.
3. `test_module3_api.py` — Fundamental, technical, and risk agent endpoints.
4. `test_news_agent.py` — Module 3 News & Sentiment Agent, Loughran-McDonald classification, DB storage.
5. `test_research_history_auto_update.py` — Audit log persistence.

---

## Application Features & Navigation

- **Dashboard (`/dashboard`)**:
  - Hero banner with quick ticker search and 1-click popular stocks (`INFY`, `TCS`, `RELIANCE`, `AAPL`, `MSFT`, `NVDA`).
  - KPI stat cards for watchlist, session queries, active agents, and supported markets.
  - Quick launch module cards.
- **Stock Research (`/stock-research`)**:
  - Live price banner with +/- % change tag and "+ Watchlist" button.
  - **Tabs**:
    - 📰 **News & Sentiment Agent**: Real-time sentiment score, executive AI summary, detected corporate announcements (M&A, earnings, regulatory), conflicting market signals alert, and verified news feed with clickable links.
    - 📈 **Interactive Chart & OHLCV**: Dynamic SVG area trend chart with bull/bear gradient fill and historical OHLCV data table.
    - 🏢 **Company Profile**: Sector, exchange, and business overview.
    - 📑 **Financial Statements**: Income Statement, Balance Sheet, and Cash Flow Statement.
    - 🛡️ **Data Audit**: Pandas 5-point data quality report and database status.
- **Watchlist (`/watchlist`)**: Add, track, and 1-click analyze saved stock symbols.
- **Research History (`/research-history`)**: Audit trail of queried companies with instant re-analyze links.
- **Preferences (`/preferences`)**: Configure default exchange (NSE, BSE, NASDAQ, NYSE) and analysis window.
