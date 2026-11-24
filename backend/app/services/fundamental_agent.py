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