# backend/app/services/fundamental_agent.py

"""
Fundamental Analysis Agent — DB-driven upgrade.

Calculates financial ratios from provided data, identifies limitations,
and returns structured FundamentalAnalysisResponse.

Design rules (from Module 3 spec):
  1. All calculations use Python arithmetic — no LLM doing math.
  2. Missing data → recorded in data_limitations, never fabricated.
  3. Output matches FundamentalAnalysisResponse schema exactly.
"""

from typing import Optional
from backend.app.schemas.fundamental import (
    FundamentalAnalysisRequest,
    FundamentalAnalysisResponse,
)


# ── Pure calculation functions (independently testable) ───────────────────────

def _safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Returns None instead of raising ZeroDivisionError."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _calc_net_margin(revenue: Optional[float], net_income: Optional[float]) -> Optional[float]:
    return _safe_divide(net_income, revenue)


def _calc_roe(net_income: Optional[float], equity: Optional[float]) -> Optional[float]:
    return _safe_divide(net_income, equity)


def _calc_debt_to_assets(total_debt: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    return _safe_divide(total_debt, total_assets)


def _calc_debt_to_equity(total_debt: Optional[float], equity: Optional[float]) -> Optional[float]:
    return _safe_divide(total_debt, equity)


def _calc_asset_turnover(revenue: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    return _safe_divide(revenue, total_assets)


def _determine_signal(
    net_margin: Optional[float],
    roe: Optional[float],
    debt_to_assets: Optional[float],
) -> str:
    """
    Rule-based fundamental signal.
    Returns: STRONG, MODERATE, WEAK, MIXED, or INSUFFICIENT_DATA.
    """
    scores = []

    if net_margin is not None:
        scores.append(1 if net_margin > 0.10 else (0 if net_margin > 0 else -1))
    if roe is not None:
        scores.append(1 if roe > 0.15 else (0 if roe > 0 else -1))
    if debt_to_assets is not None:
        scores.append(1 if debt_to_assets < 0.4 else (0 if debt_to_assets < 0.7 else -1))

    if not scores:
        return "INSUFFICIENT_DATA"

    avg = sum(scores) / len(scores)
    if avg >= 0.6:   return "STRONG"
    if avg >= 0.2:   return "MODERATE"
    if avg >= -0.2:  return "MIXED"
    return "WEAK"


def _build_profitability_summary(
    net_margin: Optional[float],
    roe: Optional[float],
    asset_turnover: Optional[float],
    ticker: str,
) -> Optional[str]:
    parts = []

    if net_margin is not None:
        pct = round(net_margin * 100, 2)
        level = "strong" if net_margin > 0.10 else ("moderate" if net_margin > 0.03 else "low")
        parts.append(f"Net profit margin is {pct}% ({level}).")
    
    if roe is not None:
        pct = round(roe * 100, 2)
        level = "efficient" if roe > 0.15 else ("adequate" if roe > 0.05 else "weak")
        parts.append(f"Return on equity is {pct}% — management is {level} at generating returns.")

    if asset_turnover is not None:
        parts.append(f"Asset turnover is {round(asset_turnover, 2)}, indicating how efficiently {ticker} uses its assets.")

    return " ".join(parts) if parts else None


def _build_stability_summary(
    debt_to_assets: Optional[float],
    debt_to_equity: Optional[float],
    total_debt: Optional[float],
    total_assets: Optional[float],
) -> Optional[str]:
    parts = []

    if debt_to_assets is not None:
        pct = round(debt_to_assets * 100, 2)
        level = "low" if debt_to_assets < 0.4 else ("moderate" if debt_to_assets < 0.7 else "high")
        parts.append(f"Debt-to-assets ratio is {pct}% ({level} leverage).")

    if debt_to_equity is not None:
        level = "conservative" if debt_to_equity < 0.5 else ("moderate" if debt_to_equity < 2.0 else "highly leveraged")
        parts.append(f"Debt-to-equity ratio is {round(debt_to_equity, 2)} — company is {level}.")

    return " ".join(parts) if parts else None


def _build_historical_comparison(net_margin: Optional[float], roe: Optional[float]) -> str:
    """
    Builds a qualitative historical context note.
    Full YoY comparison requires multi-period data (Module 4 scope).
    """
    if net_margin is None and roe is None:
        return "Historical comparison unavailable — insufficient financial data provided."
    
    notes = []
    if net_margin is not None:
        if net_margin > 0.15:
            notes.append("Net margin exceeds 15%, which is above average for most sectors.")
        elif net_margin < 0:
            notes.append("Negative net margin indicates the company is currently unprofitable.")
    
    if roe is not None:
        if roe > 0.20:
            notes.append("ROE above 20% suggests strong capital efficiency relative to industry benchmarks.")
        elif roe < 0:
            notes.append("Negative ROE indicates shareholders' equity erosion.")

    notes.append(
        "Full year-over-year comparison requires multi-period financial data "
        "and will be available in the consolidated report (Module 4)."
    )
    return " ".join(notes)


# ── Agent class ───────────────────────────────────────────────────────────────

class FundamentalAgentService:

    def analyze(
        self,
        request: FundamentalAnalysisRequest
    ) -> FundamentalAnalysisResponse:

        warnings    = []
        limitations = []

        # ── Step 1: Calculate all ratios ──────────────────────────────────────
        net_margin    = _calc_net_margin(request.revenue, request.net_income)
        roe           = _calc_roe(request.net_income, request.shareholders_equity)
        debt_to_assets = _calc_debt_to_assets(request.total_debt, request.total_assets)
        debt_to_equity = _calc_debt_to_equity(request.total_debt, request.shareholders_equity)
        asset_turnover = _calc_asset_turnover(request.revenue, request.total_assets)

        # Use provided ratios if direct calculation isn't possible
        final_pe  = request.pe_ratio
        final_pb  = request.pb_ratio
        final_roe_pct: Optional[float] = None

        if roe is not None:
            final_roe_pct = round(roe * 100, 2)
        elif request.roe is not None:
            final_roe_pct = request.roe   # use pre-calculated value from request

        # ── Step 2: Track data limitations ───────────────────────────────────
        if request.revenue is None:
            limitations.append("Revenue not provided — net margin cannot be calculated.")
        if request.net_income is None:
            limitations.append("Net income not provided — profitability metrics are limited.")
        if request.shareholders_equity is None or request.shareholders_equity == 0:
            limitations.append("Shareholders equity not provided or zero — ROE and debt-to-equity unavailable.")
        if request.total_assets is None or request.total_assets == 0:
            limitations.append("Total assets not provided — debt-to-assets and asset turnover unavailable.")
        if request.total_debt is None:
            limitations.append("Total debt not provided — financial stability metrics are limited.")
        if final_pe is None:
            limitations.append("P/E ratio not provided — valuation relative to earnings unavailable.")
        if final_pb is None:
            limitations.append("P/B ratio not provided — valuation relative to book value unavailable.")

        # ── Step 3: Validation warnings ───────────────────────────────────────
        if request.revenue is not None and request.revenue == 0:
            warnings.append("Revenue is zero — margin calculations not meaningful.")
        if request.total_debt is not None and request.total_assets is not None:
            if request.total_debt > request.total_assets:
                warnings.append("Total debt exceeds total assets — company is technically insolvent.")
        if net_margin is not None and net_margin < -0.5:
            warnings.append("Net margin below -50% — severe profitability concerns.")

        # ── Step 4: Build human-readable summaries ───────────────────────────
        profitability_summary = _build_profitability_summary(
            net_margin, roe, asset_turnover, request.ticker
        )
        financial_stability = _build_stability_summary(
            debt_to_assets, debt_to_equity,
            request.total_debt, request.total_assets
        )
        historical_note = _build_historical_comparison(net_margin, roe)

        # ── Step 5: Determine peer comparison note ───────────────────────────
        peer_note = (
            "Peer comparison requires sector benchmark data. "
            "This will be integrated in the consolidated multi-agent report."
        )

        return FundamentalAnalysisResponse(
            ticker=request.ticker,
            company_name=request.company_name,
            profitability_summary=profitability_summary,
            financial_stability=financial_stability,
            pe_ratio=final_pe,
            pb_ratio=final_pb,
            roe=final_roe_pct,
            historical_comparison=historical_note,
            peer_comparison=peer_note,
            warnings=warnings,
            data_limitations=limitations,
        )


fundamental_agent = FundamentalAgentService()

# ═══════════════════════════════════════════════════════════════════════════════
# DB-DRIVEN ENTRY POINT (added for Module 3 Priority 1)
# ═══════════════════════════════════════════════════════════════════════════════

import sys
import os as _os

# Ensure project root (Market--Team-2/) is on path so root-level modules load
_PROJECT_ROOT = _os.path.abspath(
    _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _safe_get(data: dict, *keys) -> Optional[float]:
    """
    Flexible key lookup for JSONB financial data.
    yfinance stores fields under different key names — this handles all variants.
    Returns None (never raises) if no key matches or value is non-numeric.
    """
    for k in keys:
        val = data.get(k)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                continue
    return None


def run_fundamental_from_db(
    db,                 # sqlalchemy.orm.Session
    ticker: str
) -> FundamentalAnalysisResponse:
    """
    Fully automatic DB-driven fundamental analysis.

    Flow:
      1. Fetch StockMetadata  → company name, P/E, market cap (from stock_metadata table)
      2. Fetch FinancialStatement JSONB rows → income & balance sheet data
      3. Extract financial values using flexible key lookup
      4. Derive P/B from market_cap ÷ equity when not stored directly
      5. Build FundamentalAnalysisRequest and run existing analyze()
      6. Return FundamentalAnalysisResponse with real calculated values
    """
    from backend.app.models.market_data import StockMetadata

    # Root-level FinancialStatement uses database.Base (Module 2 work)
    from models import FinancialStatement

    ticker      = ticker.upper().strip()
    limitations = []

    # ── Step 1: Company metadata ──────────────────────────────────────────────
    meta         = db.query(StockMetadata).filter(StockMetadata.ticker == ticker).first()
    company_name = meta.name    if meta else ticker
    pe_ratio     = float(meta.pe_ratio)    if (meta and meta.pe_ratio)    else None
    market_cap   = float(meta.market_cap)  if (meta and meta.market_cap)  else None

    if not meta:
        limitations.append(
            f"No company metadata found for {ticker}. "
            "Run POST /stocks/fetch/{ticker} first to populate the database."
        )

    # ── Step 2: Income Statement (most recent period) ─────────────────────────
    income_row = (
        db.query(FinancialStatement)
        .filter(
            FinancialStatement.ticker_symbol == ticker,
            FinancialStatement.statement_type == "INCOME_STATEMENT"
        )
        .order_by(FinancialStatement.period_ending.desc())
        .first()
    )
    income_data = income_row.statement_data if income_row else {}

    if not income_row:
        limitations.append(
            "No income statement found in DB. "
            "Run the Module 2 market data fetch to populate financial statements."
        )

    # ── Step 3: Balance Sheet (most recent period) ────────────────────────────
    balance_row = (
        db.query(FinancialStatement)
        .filter(
            FinancialStatement.ticker_symbol == ticker,
            FinancialStatement.statement_type == "BALANCE_SHEET"
        )
        .order_by(FinancialStatement.period_ending.desc())
        .first()
    )
    balance_data = balance_row.statement_data if balance_row else {}

    if not balance_row:
        limitations.append(
            "No balance sheet found in DB. "
            "Run the Module 2 market data fetch to populate financial statements."
        )

    # ── Step 4: Extract values with flexible key lookup ───────────────────────
    # yfinance uses different key names depending on the ticker type (US vs Indian)
    revenue = _safe_get(
        income_data,
        "Total Revenue", "totalRevenue", "Revenue"
    )
    net_income = _safe_get(
        income_data,
        "Net Income", "netIncome",
        "Net Income Common Stockholders",
        "Net Income From Continuing Operation Net Minority Interest"
    )
    total_assets = _safe_get(
        balance_data,
        "Total Assets", "totalAssets"
    )
    total_debt = _safe_get(
        balance_data,
        "Total Debt", "totalDebt",
        "Long Term Debt", "longTermDebt"
    )
    equity = _safe_get(
        balance_data,
        "Total Equity Gross Minority Interest",
        "Stockholders Equity", "totalStockholderEquity",
        "Total Stockholder Equity", "stockholdersEquity"
    )

    # ── Step 5: Derive P/B ratio from market_cap ÷ equity ────────────────────
    pb_ratio = None
    if market_cap and equity and equity > 0:
        pb_ratio = round(market_cap / equity, 4)

    # ── Step 6: Build request and run existing analyze() ─────────────────────
    request = FundamentalAnalysisRequest(
        ticker=ticker,
        company_name=company_name,
        revenue=revenue,
        net_income=net_income,
        total_assets=total_assets,
        total_debt=total_debt,
        shareholders_equity=equity,
        pe_ratio=pe_ratio,
        pb_ratio=pb_ratio,
    )

    response = fundamental_agent.analyze(request)

    # Append DB-sourced limitations to agent-generated ones
    response.data_limitations.extend(limitations)

    return response