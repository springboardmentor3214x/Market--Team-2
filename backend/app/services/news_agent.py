import re
import uuid
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
import yfinance as yf
from sqlalchemy.orm import Session

from backend.app.schemas.news import (
    NewsArticle,
    CorporateEvent,
    NewsAnalysisRequest,
    NewsAnalysisResponse,
)

# Financial sentiment keyword dictionaries (based on Loughran-McDonald financial tone analysis)
POSITIVE_KEYWORDS = {
    "growth", "surge", "surges", "profit", "profitable", "dividend", "outperform",
    "upgrade", "upgrades", "beat", "beats", "beating", "record", "bullish", "expansion",
    "all-time high", "strong results", "exceeds", "gain", "gains", "soar", "soars",
    "acquisition", "acquires", "buyback", "expansion", "innovative", "tailwind",
    "optimistic", "rebound", "rebounds", "milestone", "turnaround", "rally", "rallies"
}

NEGATIVE_KEYWORDS = {
    "decline", "declines", "slump", "slumps", "drop", "drops", "loss", "losses",
    "deficit", "downgrade", "downgrades", "miss", "misses", "bearish", "probe",
    "probes", "investigation", "lawsuit", "penalty", "penalties", "layoff", "layoffs",
    "debt crisis", "fraud", "warning", "warnings", "plunge", "plunges", "recession",
    "headwind", "cut", "cuts", "sued", "scandal", "violation", "fine", "fined",
    "pessimistic", "struggle", "struggles", "default", "defaulted", "inflation"
}

# Event Category Patterns
EVENT_PATTERNS = {
    "Earnings & Financials": [
        r"\bearnings\b", r"\bquarterly\b", r"\bq[1-4]\b", r"\bresults\b", r"\brevenue\b",
        r"\bprofit\b", r"\bguidance\b", r"\beps\b", r"\bebitda\b", r"\bdividend\b"
    ],
    "Mergers & Acquisitions (M&A)": [
        r"\bacquire[s|d]?\b", r"\bacquisition\b", r"\bmerger\b", r"\bbuyout\b",
        r"\btakeover\b", r"\bstake\b", r"\bpurchase[s|d]?\b"
    ],
    "Regulatory & Legal": [
        r"\bregulator[y]?\b", r"\bprobe[s|d]?\b", r"\bsec\b", r"\bsebi\b", r"\bantitrust\b",
        r"\blawsuit\b", r"\bcourt\b", r"\bfine[s|d]?\b", r"\bpenalty\b", r"\bcompliance\b"
    ],
    "Leadership & Governance": [
        r"\bceo\b", r"\bcfo\b", r"\bboard\b", r"\bappoint[s|ed]?\b", r"\bresign[s|ed]?\b",
        r"\bstep[s]? down\b", r"\bchairman\b", r"\bexecutive\b"
    ],
    "Partnership & Expansion": [
        r"\bpartner[s|ship]?\b", r"\bdeal\b", r"\bcontract\b", r"\balliance\b",
        r"\bjoint venture\b", r"\bexpansion\b", r"\blaunch[es|ed]?\b"
    ]
}

UNCERTAINTY_PATTERNS = [
    r"\brumor[s]?\b", r"\balleged\b", r"\bsources say\b", r"\bunconfirmed\b",
    r"\bpending approval\b", r"\bmay consider\b", r"\bpotential\b", r"\bspeculation\b"
]


class NewsAgentService:
    """
    Module 3 News and Sentiment Analysis Agent.
    Collects, cleans, classifies, and summarizes recent financial news and corporate announcements.
    """

    def classify_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Classifies financial text sentiment using weighted lexical scoring.
        Returns: (sentiment_label: 'positive'|'negative'|'neutral', score: -1.0 to 1.0)
        """
        if not text:
            return "neutral", 0.0

        words = re.findall(r"\b[a-zA-Z-]+\b", text.lower())
        pos_hits = sum(1 for w in words if w in POSITIVE_KEYWORDS)
        neg_hits = sum(1 for w in words if w in NEGATIVE_KEYWORDS)

        total_hits = pos_hits + neg_hits
        if total_hits == 0:
            return "neutral", 0.0

        score = round((pos_hits - neg_hits) / total_hits, 2)
        if score > 0.15:
            return "positive", score
        elif score < -0.15:
            return "negative", score
        else:
            return "neutral", score

    def detect_category(self, text: str) -> str:
        """
        Categorizes news headline into corporate event types.
        """
        lowered = text.lower()
        for category, patterns in EVENT_PATTERNS.items():
            for p in patterns:
                if re.search(p, lowered):
                    return category
        return "General Market News"

    def fetch_live_news(self, ticker: str, max_articles: int = 10) -> List[NewsArticle]:
        """
        Retrieves real-time news articles from verified sources via Yahoo Finance.
        Handles ticker normalization for Indian (NSE/BSE) and US (NASDAQ/NYSE) markets.
        """
        clean_ticker = ticker.strip().upper()
        # Auto-map known Indian equities if no exchange suffix
        if clean_ticker in {"INFY", "TCS", "RELIANCE", "HDFCBANK", "TATAMOTORS"}:
            yf_symbol = f"{clean_ticker}.NS"
        else:
            yf_symbol = clean_ticker

        articles: List[NewsArticle] = []
        try:
            yf_ticker = yf.Ticker(yf_symbol)
            raw_news = yf_ticker.news or []
            if not raw_news and yf_symbol != clean_ticker:
                # Try bare ticker as fallback
                yf_ticker = yf.Ticker(clean_ticker)
                raw_news = yf_ticker.news or []

            for item in raw_news[:max_articles]:
                # Handle varying yfinance news data schemas (v1 direct keys vs v2 'content' dict)
                content = item.get("content") if isinstance(item.get("content"), dict) else item
                headline = content.get("title") or item.get("title") or "Financial Update"
                summary = content.get("summary") or content.get("description") or item.get("summary")

                # Extract provider/source
                provider = content.get("provider")
                if isinstance(provider, dict):
                    source_name = provider.get("displayName") or provider.get("name") or "Financial Press"
                elif isinstance(provider, str):
                    source_name = provider
                else:
                    source_name = item.get("publisher") or "Yahoo Finance News"

                # Extract URL
                canonical = content.get("canonicalUrl")
                if isinstance(canonical, dict):
                    article_url = canonical.get("url")
                elif isinstance(canonical, str):
                    article_url = canonical
                else:
                    article_url = content.get("previewUrl") or item.get("link") or f"https://finance.yahoo.com/quote/{clean_ticker}/news"

                # Extract Published Date
                pub_time = content.get("pubDate") or item.get("providerPublishTime")
                if isinstance(pub_time, int):
                    pub_date = datetime.fromtimestamp(pub_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                elif isinstance(pub_time, str):
                    pub_date = pub_time
                else:
                    pub_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                full_text = f"{headline}. {summary or ''}"
                sentiment, score = self.classify_sentiment(full_text)
                category = self.detect_category(headline)

                articles.append(
                    NewsArticle(
                        headline=headline,
                        source=source_name,
                        published_at=pub_date,
                        url=str(article_url) if article_url else None,
                        sentiment=sentiment,
                        sentiment_score=score,
                        category=category,
                        summary=summary
                    )
                )
        except Exception as exc:
            # Non-blocking, return whatever was collected
            pass

        return articles

    def analyze(
        self,
        request: NewsAnalysisRequest,
        db: Optional[Session] = None
    ) -> NewsAnalysisResponse:
        """
        Executes News and Sentiment Analysis:
        - Uses supplied articles if present; otherwise fetches live news if auto_fetch=True or articles is None.
        - Classifies sentiment, summarizes important corporate events, identifies conflicting reports.
        - Persists to source_documents & agent_results if task_id & db are provided.
        """
        ticker = request.ticker.strip().upper()
        company_name = request.company_name

        # Fetch company profile from data_access if db provided and name not supplied
        if not company_name and db:
            try:
                import data_access
                c_info = data_access.get_company_info(db, ticker)
                if c_info:
                    company_name = c_info.get("company_name")
            except Exception:
                pass

        articles_to_process: List[NewsArticle] = []

        # 1. Determine article input source
        if request.articles is not None and len(request.articles) > 0:
            articles_to_process = list(request.articles)
        elif request.articles is None or request.auto_fetch:
            articles_to_process = self.fetch_live_news(ticker)

        # 2. Check for empty articles case
        if not articles_to_process:
            return NewsAnalysisResponse(
                ticker=ticker,
                company_name=company_name,
                overall_sentiment="insufficient_data",
                sentiment_score=0.0,
                total_articles=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                key_events=[],
                articles=[],
                corporate_events=[],
                summary="No recent news articles or announcements were available for this company.",
                conflicting_reports=[],
                warnings=["No news articles were supplied or retrieved."],
                data_limitations=["News sentiment and corporate events cannot be determined without source documents."],
                sources_saved=0
            )

        # 3. Process each article
        enriched_articles: List[NewsArticle] = []
        corporate_events: List[CorporateEvent] = []
        key_events: List[str] = []
        scores: List[float] = []

        for article in articles_to_process:
            full_text = f"{article.headline}. {article.summary or ''}"
            # If sentiment was already manually supplied, keep it; else calculate
            if article.sentiment in {"positive", "negative", "neutral"}:
                sent = article.sentiment
                score = 0.5 if sent == "positive" else (-0.5 if sent == "negative" else 0.0)
            else:
                sent, score = self.classify_sentiment(full_text)

            cat = article.category or self.detect_category(article.headline)
            enriched = article.model_copy(update={
                "sentiment": sent,
                "sentiment_score": score,
                "category": cat
            })
            enriched_articles.append(enriched)
            scores.append(score)
            key_events.append(f"[{cat}] {article.headline} ({article.source}, {article.published_at[:10] if article.published_at else 'Recent'})")

            # Extract corporate event
            if cat != "General Market News":
                corporate_events.append(
                    CorporateEvent(
                        event_type=cat,
                        headline=article.headline,
                        source=article.source,
                        published_at=article.published_at,
                        url=str(article.url) if article.url else None,
                        summary=article.summary,
                        importance="high" if cat in {"Earnings & Financials", "Mergers & Acquisitions (M&A)"} else "medium"
                    )
                )

        # 4. Compute Counts & Overall Sentiment
        positive = sum(1 for a in enriched_articles if a.sentiment == "positive")
        negative = sum(1 for a in enriched_articles if a.sentiment == "negative")
        neutral = sum(1 for a in enriched_articles if a.sentiment == "neutral")
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        if positive > 0 and negative > 0:
            overall = "mixed"
        elif positive > negative and positive >= neutral:
            overall = "positive"
        elif negative > positive and negative >= neutral:
            overall = "negative"
        else:
            overall = "neutral"

        # 5. Detect Conflicting Reports & Uncertainty
        conflicting_reports: List[str] = []
        if positive > 0 and negative > 0:
            conflicting_reports.append(
                f"Articles contain divergent viewpoints: {positive} positive vs {negative} negative report(s) identified."
            )

        # Check for unconfirmed rumors or speculation
        uncertainties = []
        for a in enriched_articles:
            for pattern in UNCERTAINTY_PATTERNS:
                if re.search(pattern, a.headline.lower()) or (a.summary and re.search(pattern, a.summary.lower())):
                    uncertainties.append(f"Uncertainty detected in: '{a.headline[:60]}...' ({a.source})")
                    break

        if uncertainties:
            conflicting_reports.extend(uncertainties[:3])

        # 6. Generate Executive Summary
        event_highlights = f" Highlighted events include {len(corporate_events)} corporate event(s)." if corporate_events else ""
        summary = (
            f"Analyzed {len(enriched_articles)} articles for {ticker}: "
            f"{positive} positive, {negative} negative and {neutral} neutral."
            f" Overall market sentiment is classified as {overall.upper()} (Score: {avg_score:+0.2f})."
            f"{event_highlights}"
        )

        # 7. Optional Database Persistence (Module 3 Tables)
        sources_saved = 0
        if db and request.task_id:
            try:
                import crud
                import models

                task_uuid = uuid.UUID(str(request.task_id))
                source_records = []
                for a in enriched_articles:
                    source_records.append({
                        "source_type": models.SourceType.NEWS_ARTICLE.value,
                        "source_url": str(a.url) if a.url else f"https://finance.yahoo.com/quote/{ticker}",
                        "title": a.headline,
                        "published_at": datetime.now(timezone.utc)
                    })

                sources_saved = crud.bulk_save_source_documents(db, task_uuid, source_records)

                # Persist Agent Result
                crud.upsert_agent_result(
                    db=db,
                    task_id=task_uuid,
                    agent_name=models.AgentName.NEWS,
                    status=models.AgentStatus.COMPLETED,
                    output_json={
                        "overall_sentiment": overall,
                        "sentiment_score": avg_score,
                        "total_articles": len(enriched_articles),
                        "positive": positive,
                        "negative": negative,
                        "neutral": neutral,
                        "summary": summary,
                        "corporate_events_count": len(corporate_events)
                    }
                )
            except Exception as db_err:
                # Log without failing analysis
                pass

        return NewsAnalysisResponse(
            ticker=ticker,
            company_name=request.company_name,
            overall_sentiment=overall,
            sentiment_score=avg_score,
            total_articles=len(enriched_articles),
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            key_events=key_events,
            articles=enriched_articles,
            corporate_events=corporate_events,
            summary=summary,
            conflicting_reports=conflicting_reports,
            warnings=[],
            data_limitations=[],
            sources_saved=sources_saved
        )


news_agent = NewsAgentService()
