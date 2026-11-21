
from backend.app.schemas.news import (
    NewsAnalysisRequest,
    NewsAnalysisResponse,
)


class NewsAgentService:

    def analyze(
        self,
        request: NewsAnalysisRequest
    ) -> NewsAnalysisResponse:

        articles = request.articles

        if not articles:
            return NewsAnalysisResponse(
                ticker=request.ticker,
                overall_sentiment="insufficient_data",
                total_articles=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                warnings=["No news articles were supplied."],
                data_limitations=["News sentiment cannot be determined."]
            )

        positive = sum(
            1 for article in articles
            if article.sentiment == "positive"
        )

        negative = sum(
            1 for article in articles
            if article.sentiment == "negative"
        )

        neutral = sum(
            1 for article in articles
            if article.sentiment == "neutral"
        )

        if positive > 0 and negative > 0:
            overall = "mixed"
        elif positive > negative and positive > neutral:
            overall = "positive"
        elif negative > positive and negative > neutral:
            overall = "negative"
        else:
            overall = "neutral"

        conflicting_reports = []

        if positive > 0 and negative > 0:
            conflicting_reports.append(
                "Articles contain both positive and negative sentiment."
            )

        key_events = [
            article.headline for article in articles
        ]

        summary = (
            f"Analyzed {len(articles)} articles: "
            f"{positive} positive, "
            f"{negative} negative and "
            f"{neutral} neutral."
        )

        return NewsAnalysisResponse(
            ticker=request.ticker,
            overall_sentiment=overall,
            total_articles=len(articles),
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            key_events=key_events,
            summary=summary,
            conflicting_reports=conflicting_reports,
            warnings=[],
            data_limitations=[]
        )


news_agent = NewsAgentService()
