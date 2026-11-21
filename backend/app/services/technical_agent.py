
import numpy as np
import pandas as pd

from backend.app.schemas.technical import (
    TechnicalAnalysisRequest,
    TechnicalAnalysisResponse,
)


class TechnicalAgentService:

    def analyze(
        self,
        request: TechnicalAnalysisRequest,
        historical_data: list
    ) -> TechnicalAnalysisResponse:

        if not historical_data:
            return TechnicalAnalysisResponse(
                ticker=request.ticker,
                signal="insufficient_data",
                warnings=["No historical stock data available."],
                data_limitations=["Technical indicators cannot be calculated."]
            )

        df = pd.DataFrame(historical_data)

        if "close" not in df.columns:
            raise ValueError("Historical data must contain a close column.")

        close = pd.to_numeric(df["close"], errors="coerce").dropna()

        if len(close) < max(request.sma_period, request.ema_period, request.rsi_period) + 1:
            return TechnicalAnalysisResponse(
                ticker=request.ticker,
                signal="insufficient_data",
                warnings=["Not enough historical prices to calculate indicators."]
            )

        sma = close.rolling(window=request.sma_period).mean().iloc[-1]

        ema = close.ewm(
            span=request.ema_period,
            adjust=False
        ).mean().iloc[-1]

        delta = close.diff()

        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)

        avg_gain = gains.rolling(window=request.rsi_period).mean()
        avg_loss = losses.rolling(window=request.rsi_period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi_series = 100 - (100 / (1 + rs))

        rsi = rsi_series.iloc[-1]

        if pd.isna(rsi):
            if avg_loss.iloc[-1] == 0 and avg_gain.iloc[-1] > 0:
                rsi = 100.0
            elif avg_gain.iloc[-1] == 0 and avg_loss.iloc[-1] > 0:
                rsi = 0.0

        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()

        macd_series = ema_12 - ema_26
        signal_series = macd_series.ewm(span=9, adjust=False).mean()

        macd = macd_series.iloc[-1]
        macd_signal = signal_series.iloc[-1]

        daily_returns = close.pct_change().dropna()

        volatility = (
            daily_returns.std() * np.sqrt(252) * 100
            if len(daily_returns) > 1 else None
        )

        if pd.isna(volatility):
            volatility = None

        bullish = (
            close.iloc[-1] > sma
            and macd > macd_signal
            and rsi is not None
            and rsi < 70
        )

        bearish = (
            close.iloc[-1] < sma
            and macd < macd_signal
            and rsi is not None
            and rsi > 30
        )

        signal = (
            "bullish" if bullish
            else "bearish" if bearish
            else "neutral"
        )

        return TechnicalAnalysisResponse(
            ticker=request.ticker,
            sma=round(float(sma), 4),
            ema=round(float(ema), 4),
            rsi=round(float(rsi), 4) if rsi is not None else None,
            macd=round(float(macd), 4),
            macd_signal=round(float(macd_signal), 4),
            historical_volatility=round(float(volatility), 4) if volatility is not None else None,
            signal=signal,
            explanation="Signal is based on historical SMA, MACD and RSI conditions. It is not a guaranteed prediction.",
            warnings=[],
            data_limitations=[]
        )


technical_agent = TechnicalAgentService()
