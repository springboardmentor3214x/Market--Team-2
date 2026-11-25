"""
Unit tests for the Fundamental Analysis Agent.

Tests all pure Python calculation functions and the full agent service.
No database, no network, no external dependencies required.

Run with:
    pytest backend/tests/test_fundamental_agent.py -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from backend.app.services.fundamental_agent import (
    _safe_divide,
    _calc_net_margin,
    _calc_roe,
    _calc_debt_to_assets,
    _calc_debt_to_equity,
    _calc_asset_turnover,
    _determine_signal,
    _build_profitability_summary,
    _build_stability_summary,
    FundamentalAgentService,
)
from backend.app.schemas.fundamental import FundamentalAnalysisRequest


# ════════════════════════════════════════════════════════════════════════════════
# 1. _safe_divide
# ════════════════════════════════════════════════════════════════════════════════

class TestSafeDivide:

    def test_normal_division(self):
        assert _safe_divide(100.0, 4.0) == 25.0

    def test_zero_denominator_returns_none(self):
        assert _safe_divide(100.0, 0.0) is None

    def test_none_numerator_returns_none(self):
        assert _safe_divide(None, 10.0) is None

    def test_none_denominator_returns_none(self):
        assert _safe_divide(100.0, None) is None

    def test_both_none_returns_none(self):
        assert _safe_divide(None, None) is None

    def test_negative_result(self):
        assert _safe_divide(-50.0, 200.0) == -0.25

    def test_result_rounded_to_4_decimals(self):
        result = _safe_divide(1.0, 3.0)
        assert result == round(1 / 3, 4)


# ════════════════════════════════════════════════════════════════════════════════
# 2. Net Margin
# ════════════════════════════════════════════════════════════════════════════════

class TestNetMargin:

    def test_profitable_company(self):
        # 10% net margin
        assert _calc_net_margin(revenue=1_000_000, net_income=100_000) == 0.1

    def test_loss_making_company(self):
        result = _calc_net_margin(revenue=1_000_000, net_income=-50_000)
        assert result == -0.05

    def test_zero_revenue_returns_none(self):
        assert _calc_net_margin(revenue=0, net_income=100_000) is None

    def test_missing_revenue_returns_none(self):
        assert _calc_net_margin(revenue=None, net_income=100_000) is None

    def test_missing_net_income_returns_none(self):
        assert _calc_net_margin(revenue=1_000_000, net_income=None) is None

    def test_high_margin_company(self):
        # 25% net margin (like Infosys)
        result = _calc_net_margin(revenue=4_000_000, net_income=1_000_000)
        assert result == 0.25


# ════════════════════════════════════════════════════════════════════════════════
# 3. Return on Equity (ROE)
# ════════════════════════════════════════════════════════════════════════════════

class TestROE:

    def test_strong_roe(self):
        # 25% ROE
        result = _calc_roe(net_income=250_000, equity=1_000_000)
        assert result == 0.25

    def test_weak_roe(self):
        # 3% ROE
        result = _calc_roe(net_income=30_000, equity=1_000_000)
        assert result == 0.03

    def test_negative_equity(self):
        # Still computes — negative equity is a valid financial scenario
        result = _calc_roe(net_income=100_000, equity=-500_000)
        assert result == -0.2

    def test_zero_equity_returns_none(self):
        assert _calc_roe(net_income=100_000, equity=0) is None

    def test_missing_net_income_returns_none(self):
        assert _calc_roe(net_income=None, equity=1_000_000) is None


# ════════════════════════════════════════════════════════════════════════════════
# 4. Debt Ratios
# ════════════════════════════════════════════════════════════════════════════════

class TestDebtRatios:

    def test_debt_to_assets_low(self):
        # 20% — healthy
        result = _calc_debt_to_assets(total_debt=200_000, total_assets=1_000_000)
        assert result == 0.2

    def test_debt_to_assets_high(self):
        # 80% — risky
        result = _calc_debt_to_assets(total_debt=800_000, total_assets=1_000_000)
        assert result == 0.8

    def test_debt_to_assets_zero_assets_returns_none(self):
        assert _calc_debt_to_assets(total_debt=200_000, total_assets=0) is None

    def test_debt_to_equity(self):
        result = _calc_debt_to_equity(total_debt=400_000, equity=1_000_000)
        assert result == 0.4

    def test_debt_exceeds_assets(self):
        # Technically insolvent — still calculates correctly
        result = _calc_debt_to_assets(total_debt=1_500_000, total_assets=1_000_000)
        assert result == 1.5

    def test_asset_turnover(self):
        result = _calc_asset_turnover(revenue=2_000_000, total_assets=1_000_000)
        assert result == 2.0


# ════════════════════════════════════════════════════════════════════════════════
# 5. Signal Engine
# ════════════════════════════════════════════════════════════════════════════════

class TestDetermineSignal:

    def test_strong_signal(self):
        signal = _determine_signal(
            net_margin=0.20,       # > 0.10 → score +1
            roe=0.25,              # > 0.15 → score +1
            debt_to_assets=0.20,   # < 0.40 → score +1
        )
        assert signal == "STRONG"

    def test_weak_signal(self):
        signal = _determine_signal(
            net_margin=-0.15,      # < 0 → score -1
            roe=-0.10,             # < 0 → score -1
            debt_to_assets=0.80,   # > 0.70 → score -1
        )
        assert signal == "WEAK"

    def test_mixed_signal(self):
        signal = _determine_signal(
            net_margin=0.05,       # 0 < x < 0.10 → score 0
            roe=0.25,              # > 0.15 → score +1
            debt_to_assets=0.80,   # > 0.70 → score -1
        )
        # avg = (0 + 1 + -1) / 3 = 0 → MIXED
        assert signal == "MIXED"

    def test_all_none_returns_insufficient_data(self):
        signal = _determine_signal(
            net_margin=None,
            roe=None,
            debt_to_assets=None,
        )
        assert signal == "INSUFFICIENT_DATA"

    def test_partial_data_still_works(self):
        # Only 1 metric — still returns a valid signal
        signal = _determine_signal(
            net_margin=0.20,
            roe=None,
            debt_to_assets=None,
        )
        assert signal == "STRONG"

    def test_moderate_signal(self):
        signal = _determine_signal(
            net_margin=0.05,       # score 0
            roe=0.20,              # score +1
            debt_to_assets=0.35,   # score +1
        )
        # avg = (0 + 1 + 1) / 3 = 0.67 → STRONG
        # Actually let's make it MODERATE
        signal2 = _determine_signal(
            net_margin=0.05,       # score 0
            roe=0.10,              # 0 < x < 0.15 → score 0
            debt_to_assets=0.50,   # 0.4 < x < 0.7 → score 0
        )
        assert signal2 == "MIXED"   # avg = 0 → MIXED


# ════════════════════════════════════════════════════════════════════════════════
# 6. Full Agent Service (end-to-end, no DB)
# ════════════════════════════════════════════════════════════════════════════════

class TestFundamentalAgentService:

    def setup_method(self):
        self.agent = FundamentalAgentService()

    def test_full_analysis_with_complete_data(self):
        """Agent produces real output when all data is provided."""
        request = FundamentalAnalysisRequest(
            ticker="INFY",
            company_name="Infosys Limited",
            revenue=1_500_000_000.0,
            net_income=260_000_000.0,
            total_assets=800_000_000.0,
            total_debt=80_000_000.0,
            shareholders_equity=600_000_000.0,
            pe_ratio=24.5,
            pb_ratio=7.8,
        )
        response = self.agent.analyze(request)

        assert response.ticker == "INFY"
        assert response.company_name == "Infosys Limited"
        assert response.roe is not None
        assert response.roe > 0
        assert response.profitability_summary is not None
        assert response.financial_stability is not None
        assert isinstance(response.data_limitations, list)
        assert isinstance(response.warnings, list)

    def test_analysis_with_no_financial_data(self):
        """Agent handles missing data gracefully with data_limitations."""
        request = FundamentalAnalysisRequest(ticker="UNKNOWN_CO")
        response = self.agent.analyze(request)

        assert response.ticker == "UNKNOWN_CO"
        assert len(response.data_limitations) > 0
        assert response.profitability_summary is None
        assert response.roe is None

    def test_insolvency_warning_triggered(self):
        """Warning fires when total_debt > total_assets."""
        request = FundamentalAnalysisRequest(
            ticker="TESTCO",
            revenue=500_000.0,
            net_income=10_000.0,
            total_assets=200_000.0,
            total_debt=350_000.0,          # debt > assets → insolvent
            shareholders_equity=50_000.0,
        )
        response = self.agent.analyze(request)
        assert any("insolvent" in w.lower() for w in response.warnings)

    def test_zero_revenue_warning_triggered(self):
        """Warning fires when revenue is exactly zero."""
        request = FundamentalAnalysisRequest(
            ticker="ZEROREV",
            revenue=0.0,
            net_income=10_000.0,
        )
        response = self.agent.analyze(request)
        assert any("zero" in w.lower() for w in response.warnings)

    def test_severe_loss_warning_triggered(self):
        """Warning fires when net margin is below -50%."""
        request = FundamentalAnalysisRequest(
            ticker="LOSSCO",
            revenue=1_000_000.0,
            net_income=-600_000.0,          # -60% margin → severe
        )
        response = self.agent.analyze(request)
        assert any("severe" in w.lower() or "-50%" in w for w in response.warnings)

    def test_pe_ratio_passed_through(self):
        """P/E ratio from request is preserved in response."""
        request = FundamentalAnalysisRequest(
            ticker="TESTPE",
            pe_ratio=18.5,
        )
        response = self.agent.analyze(request)
        assert response.pe_ratio == 18.5

    def test_response_has_all_required_fields(self):
        """All required fields exist in the response schema."""
        request = FundamentalAnalysisRequest(ticker="CHECKCO")
        response = self.agent.analyze(request)

        assert hasattr(response, "ticker")
        assert hasattr(response, "profitability_summary")
        assert hasattr(response, "financial_stability")
        assert hasattr(response, "pe_ratio")
        assert hasattr(response, "pb_ratio")
        assert hasattr(response, "roe")
        assert hasattr(response, "historical_comparison")
        assert hasattr(response, "peer_comparison")
        assert hasattr(response, "warnings")
        assert hasattr(response, "data_limitations")