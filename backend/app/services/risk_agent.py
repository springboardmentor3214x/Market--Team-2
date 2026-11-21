
from backend.app.schemas.risk import (
    RiskAnalysisRequest,
    RiskAnalysisResponse,
)


class RiskAgentService:

    def analyze(
        self,
        request: RiskAnalysisRequest
    ) -> RiskAnalysisResponse:

        warnings = []
        limitations = []

        volatility = request.historical_volatility
        drawdown = request.maximum_drawdown

        # Assess volatility risk
        if volatility is None:
            volatility_risk = "Unknown"
            limitations.append("Historical volatility is unavailable.")
        elif volatility < 15:
            volatility_risk = "Low"
        elif volatility < 30:
            volatility_risk = "Moderate"
        elif volatility < 50:
            volatility_risk = "High"
        else:
            volatility_risk = "Very high"

        # Determine overall risk using available measurements
        risk_scores = []

        if volatility is not None:
            if volatility < 15:
                risk_scores.append(1)
            elif volatility < 30:
                risk_scores.append(2)
            elif volatility < 50:
                risk_scores.append(3)
            else:
                risk_scores.append(4)

        if drawdown is not None:
            if drawdown < 0.10:
                risk_scores.append(1)
            elif drawdown < 0.20:
                risk_scores.append(2)
            elif drawdown < 0.35:
                risk_scores.append(3)
            else:
                risk_scores.append(4)

        if not risk_scores:
            overall_risk = "undetermined"
            warnings.append(
                "Insufficient numerical data to determine overall risk."
            )
        else:
            average_score = sum(risk_scores) / len(risk_scores)

            if average_score < 1.5:
                overall_risk = "low"
            elif average_score < 2.5:
                overall_risk = "moderate"
            elif average_score < 3.5:
                overall_risk = "high"
            else:
                overall_risk = "very_high"

        major_risks = (
            request.financial_risks + request.sector_risks
        )

        if request.agent_conflicts:
            warnings.append(
                "Conflicting findings were received from other agents."
            )

        if request.missing_data:
            limitations.extend(request.missing_data)

        alternative_scenarios = [
            "Market volatility may increase during uncertain market conditions.",
            "Changes in financial performance may affect the company's risk profile."
        ]

        explanation = (
            "Risk classification is based on the available volatility "
            "and maximum drawdown measurements. It is not a guarantee "
            "of future performance."
        )

        return RiskAnalysisResponse(
            ticker=request.ticker,
            risk_level=overall_risk,
            historical_volatility=volatility,
            maximum_drawdown=drawdown,
            major_risks=major_risks,
            alternative_scenarios=alternative_scenarios,
            agent_conflicts=request.agent_conflicts,
            explanation=explanation,
            warnings=warnings,
            data_limitations=limitations
        )


risk_agent = RiskAgentService()
