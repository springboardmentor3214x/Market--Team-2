
from backend.app.schemas.fundamental import (
    FundamentalAnalysisRequest,
    FundamentalAnalysisResponse,
)


class FundamentalAgentService:

    def analyze(
        self,
        request: FundamentalAnalysisRequest
    ) -> FundamentalAnalysisResponse:

        warnings = []
        limitations = []

        profitability = None
        stability = None

        roe = request.roe

        if request.revenue is not None and request.net_income is not None:
            if request.revenue > 0:
                margin = (request.net_income / request.revenue) * 100
                profitability = (
                    f"Net profit margin is {margin:.2f}%."
                )
            else:
                warnings.append("Revenue must be positive to calculate profit margin.")
        else:
            limitations.append("Revenue or net income is missing.")

        if (
            request.total_debt is not None
            and request.total_assets is not None
        ):
            if request.total_assets > 0:
                debt_ratio = (
                    request.total_debt / request.total_assets
                ) * 100

                stability = (
                    f"Debt-to-assets ratio is {debt_ratio:.2f}%."
                )
            else:
                warnings.append("Total assets must be positive.")
        else:
            limitations.append("Debt or total assets data is missing.")

        if (
            roe is None
            and request.net_income is not None
            and request.shareholders_equity is not None
            and request.shareholders_equity > 0
        ):
            roe = (
                request.net_income / request.shareholders_equity
            ) * 100

        if roe is None:
            limitations.append("ROE could not be calculated.")

        return FundamentalAnalysisResponse(
            ticker=request.ticker,
            company_name=request.company_name,
            profitability_summary=profitability,
            financial_stability=stability,
            pe_ratio=request.pe_ratio,
            pb_ratio=request.pb_ratio,
            roe=round(roe, 2) if roe is not None else None,
            historical_comparison=None,
            peer_comparison=None,
            warnings=warnings,
            data_limitations=limitations
        )


fundamental_agent = FundamentalAgentService()
