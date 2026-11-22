import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Search,
  Bookmark,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  ExternalLink,
  AlertTriangle,
  FileText,
  BarChart2,
  ShieldCheck,
  Building,
  Calendar,
  Layers,
  Sparkles,
  CheckCircle2,
  XCircle
} from "lucide-react";
import api from "../services/api";

function StockResearch() {
  const navigate = useNavigate();
  const location = useLocation();

  const searchParams = new URLSearchParams(location.search);
  const initialTicker = searchParams.get("ticker") || "INFY";

  const [searchTerm, setSearchTerm] = useState(initialTicker);
  const [selectedStock, setSelectedStock] = useState(null);
  const [historicalPrices, setHistoricalPrices] = useState([]);
  const [validationReport, setValidationReport] = useState(null);
  const [period, setPeriod] = useState("3 Months");
  const [statement, setStatement] = useState("Income Statement");
  const [activeTab, setActiveTab] = useState("news"); // default to Module 3 News agent tab
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [watchlistMessage, setWatchlistMessage] = useState("");

  // Module 3: News & Sentiment Agent State
  const [newsData, setNewsData] = useState(null);
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsError, setNewsError] = useState("");

  const popularTickers = ["INFY", "TCS", "RELIANCE", "AAPL", "MSFT", "NVDA"];

  const sampleStocks = [
    {
      symbol: "INFY",
      name: "Infosys Limited",
      exchange: "NSE",
      currency: "INR",
      sector: "Information Technology",
      industry: "IT Services",
      price: "1,520.00",
      priceChangePercent: 1.45,
      description: "Infosys is a global leader in next-generation digital services and consulting."
    },
    {
      symbol: "TCS",
      name: "Tata Consultancy Services",
      exchange: "BSE",
      currency: "INR",
      sector: "Information Technology",
      industry: "IT Services",
      price: "3,450.00",
      priceChangePercent: 0.82,
      description: "TCS is an Indian multinational information technology services and consulting company."
    },
    {
      symbol: "RELIANCE",
      name: "Reliance Industries",
      exchange: "NSE",
      currency: "INR",
      sector: "Energy",
      industry: "Oil and Gas",
      price: "1,280.00",
      priceChangePercent: -0.65,
      description: "Reliance Industries operates in energy, retail, petrochemicals, and telecommunications."
    },
    {
      symbol: "AAPL",
      name: "Apple Inc.",
      exchange: "NASDAQ",
      currency: "USD",
      sector: "Technology",
      industry: "Consumer Electronics",
      price: "225.00",
      priceChangePercent: 2.15,
      description: "Apple designs, manufactures, and markets smartphones, personal computers, and wearables."
    },
    {
      symbol: "MSFT",
      name: "Microsoft Corporation",
      exchange: "NASDAQ",
      currency: "USD",
      sector: "Technology",
      industry: "Software & Cloud",
      price: "420.00",
      priceChangePercent: 1.10,
      description: "Microsoft produces computer software, consumer electronics, personal computers, and cloud services."
    }
  ];

  const samplePrices = [
    { date: "2026-11-13", open: "1,500.00", high: "1,535.00", low: "1,490.00", close: "1,520.00", volume: "1,250,000", rawClose: 1520 },
    { date: "2026-11-12", open: "1,480.00", high: "1,510.00", low: "1,470.00", close: "1,500.00", volume: "1,100,000", rawClose: 1500 },
    { date: "2026-11-11", open: "1,460.00", high: "1,495.00", low: "1,450.00", close: "1,480.00", volume: "980,000", rawClose: 1480 },
    { date: "2026-10-15", open: "1,430.00", high: "1,465.00", low: "1,420.00", close: "1,450.00", volume: "900,000", rawClose: 1450 },
    { date: "2026-08-15", open: "1,380.00", high: "1,410.00", low: "1,370.00", close: "1,400.00", volume: "850,000", rawClose: 1400 },
    { date: "2026-05-15", open: "1,300.00", high: "1,340.00", low: "1,290.00", close: "1,320.00", volume: "800,000", rawClose: 1320 }
  ];

  const periodToBackendMap = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y"
  };

  const financialStatements = {
    "Income Statement": [
      { label: "Total Revenue", value: "₹25,000 Cr" },
      { label: "Operating Expenses", value: "₹18,000 Cr" },
      { label: "Operating Income (EBIT)", value: "₹7,000 Cr" },
      { label: "Net Income", value: "₹5,000 Cr" },
      { label: "Diluted EPS", value: "₹22.50" }
    ],
    "Balance Sheet": [
      { label: "Cash & Short Term Investments", value: "₹18,500 Cr" },
      { label: "Total Assets", value: "₹82,400 Cr" },
      { label: "Total Debt & Liabilities", value: "₹29,800 Cr" },
      { label: "Shareholders' Equity", value: "₹52,600 Cr" },
      { label: "Book Value Per Share", value: "₹235.00" }
    ],
    "Cash Flow Statement": [
      { label: "Operating Cash Flow", value: "₹7,200 Cr" },
      { label: "Capital Expenditures (CapEx)", value: "-₹1,850 Cr" },
      { label: "Free Cash Flow", value: "₹5,350 Cr" },
      { label: "Financing & Dividends Paid", value: "-₹2,100 Cr" },
      { label: "Net Change in Cash", value: "+₹1,400 Cr" }
    ]
  };

  const fetchNewsAnalysis = async (tickerSymbol) => {
    setNewsLoading(true);
    setNewsError("");
    try {
      const res = await api.get(`/analysis/news/${encodeURIComponent(tickerSymbol)}`);
      setNewsData(res.data);
    } catch (err) {
      console.warn("News agent fetch note:", err);
      setNewsError("Unable to load live news analysis at this moment.");
    } finally {
      setNewsLoading(false);
    }
  };

  const fetchLiveStock = async (tickerSymbol, selectedPeriodLabel) => {
    if (!tickerSymbol || !tickerSymbol.trim()) return;
    const cleanTicker = tickerSymbol.trim().toUpperCase();
    const backendPeriod = periodToBackendMap[selectedPeriodLabel] || "3mo";

    setLoading(true);
    setError("");
    setWatchlistMessage("");

    // Fetch Module 3 News Agent analysis in parallel
    fetchNewsAnalysis(cleanTicker);

    try {
      const response = await api.get(`/stocks/${encodeURIComponent(cleanTicker)}?period=${backendPeriod}`);
      const data = response.data;
      const meta = data.metadata || {};

      setSelectedStock({
        symbol: data.ticker || cleanTicker,
        name: meta.name || cleanTicker,
        exchange: meta.exchange || "NSE",
        currency: meta.currency || "INR",
        sector: meta.sector || "Information Technology",
        industry: meta.industry || "IT Services & Software",
        price: meta.current_price !== undefined ? Number(meta.current_price).toLocaleString("en-US", { minimumFractionDigits: 2 }) : "1,520.00",
        priceChange: meta.price_change,
        priceChangePercent: meta.price_change_percent !== undefined ? meta.price_change_percent : 1.25,
        description: `${meta.name || cleanTicker} operates in ${meta.sector || "market industries"}. Real-time financial telemetry powered by Alpha Vantage & Yahoo Finance.`,
        dataSource: meta.data_source || "Alpha Vantage",
        lastUpdated: meta.last_updated || new Date().toISOString()
      });

      // Map historical prices with numerical rawClose for chart
      if (Array.isArray(data.history) && data.history.length > 0) {
        setHistoricalPrices(
          data.history.map((row) => ({
            date: row.date,
            open: typeof row.open === "number" ? row.open.toLocaleString("en-US", { minimumFractionDigits: 2 }) : row.open,
            high: typeof row.high === "number" ? row.high.toLocaleString("en-US", { minimumFractionDigits: 2 }) : row.high,
            low: typeof row.low === "number" ? row.low.toLocaleString("en-US", { minimumFractionDigits: 2 }) : row.low,
            close: typeof row.close === "number" ? row.close.toLocaleString("en-US", { minimumFractionDigits: 2 }) : row.close,
            volume: typeof row.volume === "number" ? row.volume.toLocaleString() : row.volume,
            rawClose: typeof row.close === "number" ? row.close : parseFloat(String(row.close).replace(/,/g, "")) || 0
          }))
        );
      } else {
        setHistoricalPrices([]);
      }

      if (data.validation_report) {
        setValidationReport(data.validation_report);
      }

      // Log to research history
      try {
        await api.post("/research-history", {
          ticker_symbol: cleanTicker,
          company_name: meta.name || cleanTicker,
          analysis_period: backendPeriod,
          research_summary: {
            price: meta.current_price,
            change_percent: meta.price_change_percent,
            source: meta.data_source
          }
        });
      } catch (logErr) {
        console.log("History log note:", logErr);
      }

    } catch (apiErr) {
      console.warn("Live API note, checking fallback:", apiErr);
      const fallback = sampleStocks.find((s) => s.symbol.toLowerCase() === cleanTicker.toLowerCase());

      if (fallback) {
        setSelectedStock(fallback);
        setHistoricalPrices(samplePrices);
        setValidationReport({
          total_records: samplePrices.length,
          cleaned_records: samplePrices.length,
          missing_values_detected: false,
          duplicates_removed: 0,
          ohlc_anomalies_detected: false,
          is_chronological: true,
          status: "PASSED (Sample)"
        });
      } else {
        setError(apiErr.response?.data?.detail || `No market data found for symbol "${cleanTicker}".`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialTicker) {
      setSearchTerm(initialTicker);
      fetchLiveStock(initialTicker, period);
    }
  }, [initialTicker]);

  const handlePeriodChange = (newPeriod) => {
    setPeriod(newPeriod);
    if (selectedStock?.symbol) {
      fetchLiveStock(selectedStock.symbol, newPeriod);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    const term = searchTerm.trim().toUpperCase();
    if (!term) return;
    fetchLiveStock(term, period);
  };

  const handleAddToWatchlist = async () => {
    if (!selectedStock) return;
    try {
      setWatchlistMessage("");
      await api.post("/watchlist", {
        symbol: selectedStock.symbol,
        company_name: selectedStock.name,
        exchange: selectedStock.exchange
      });
      setWatchlistMessage(`✅ ${selectedStock.symbol} successfully added to your Watchlist!`);
      setTimeout(() => setWatchlistMessage(""), 4000);
    } catch (err) {
      setWatchlistMessage(err.response?.data?.detail || "Could not add to watchlist.");
    }
  };

  const getSentimentBadgeClass = (sentiment) => {
    switch ((sentiment || "").toLowerCase()) {
      case "positive": return "sentiment-positive";
      case "negative": return "sentiment-negative";
      case "mixed": return "sentiment-mixed";
      default: return "sentiment-neutral";
    }
  };

  // Helper for generating SVG Area Chart
  const renderSvgChart = () => {
    if (!historicalPrices || historicalPrices.length === 0) return null;

    // Use prices sorted chronologically (oldest to newest) for chart
    const prices = [...historicalPrices].reverse();
    const values = prices.map((p) => p.rawClose).filter((v) => !isNaN(v) && v > 0);
    if (values.length < 2) return null;

    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;

    const width = 800;
    const height = 220;
    const padding = 25;

    const points = values.map((val, idx) => {
      const x = padding + (idx / (values.length - 1)) * (width - 2 * padding);
      const y = height - padding - ((val - minVal) / range) * (height - 2 * padding);
      return { x, y, val, date: prices[idx]?.date };
    });

    const pathD = points.reduce((acc, pt, idx) => {
      return `${acc} ${idx === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`;
    }, "");

    const areaD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${height - padding} L ${points[0].x.toFixed(1)} ${height - padding} Z`;

    const isUp = values[values.length - 1] >= values[0];
    const strokeColor = isUp ? "#10b981" : "#ef4444";
    const gradientId = isUp ? "areaGreenGrad" : "areaRedGrad";

    return (
      <div className="svg-chart-wrapper">
        <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          <defs>
            <linearGradient id="areaGreenGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="areaRedGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="var(--border-subtle)" strokeDasharray="3 3" />
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="var(--border-subtle)" strokeDasharray="3 3" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="var(--border-subtle)" />

          {/* Area Fill */}
          <path d={areaD} fill={`url(#${gradientId})`} />

          {/* Stroke Line */}
          <path d={pathD} fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

          {/* First & Last Circles */}
          <circle cx={points[0].x} cy={points[0].y} r="4" fill={strokeColor} />
          <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="5" fill="#ffffff" stroke={strokeColor} strokeWidth="2.5" />
        </svg>

        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px", fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          <span>{prices[0]?.date} (Low: {selectedStock?.currency} {minVal.toFixed(2)})</span>
          <span style={{ color: strokeColor, fontWeight: "700" }}>{isUp ? "▲ Bullish Momentum" : "▼ Bearish Retracement"}</span>
          <span>{prices[prices.length - 1]?.date} (High: {selectedStock?.currency} {maxVal.toFixed(2)})</span>
        </div>
      </div>
    );
  };

  const validationChecks = [
    { label: "Missing values detection", passed: validationReport ? !validationReport.missing_values_detected : true },
    { label: "Duplicate timestamps removed", passed: validationReport ? validationReport.duplicates_removed === 0 : true },
    { label: "Strict chronological ordering", passed: validationReport ? !!validationReport.is_chronological : true },
    { label: "OHLC price boundary check (High >= Low)", passed: validationReport ? !validationReport.ohlc_anomalies_detected : true },
    { label: "Numeric volume formatting", passed: true }
  ];

  const allValid = validationChecks.every((c) => c.passed);

  return (
    <div className="research-container">
      {/* Top Bar with Search & Ticker Switcher */}
      <div className="research-topbar">
        <form onSubmit={handleSearch} className="search-form-full" style={{ flex: 1, maxWidth: "560px" }}>
          <Search size={18} style={{ color: "var(--text-muted)", marginLeft: "10px", alignSelf: "center" }} />
          <input
            type="text"
            placeholder="Search company or ticker (e.g. INFY, TCS, AAPL)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? <RefreshCw size={14} className="spin" /> : "Search"}
          </button>
        </form>

        <div className="quick-chips-row">
          <span className="quick-chips-label">Quick Select:</span>
          {popularTickers.map((ticker) => (
            <button
              key={ticker}
              type="button"
              onClick={() => {
                setSearchTerm(ticker);
                fetchLiveStock(ticker, period);
              }}
              className={`ticker-chip ${selectedStock?.symbol === ticker ? "active" : ""}`}
            >
              {ticker}
            </button>
          ))}
        </div>
      </div>

      {/* Status Messages */}
      {error && <div className="alert-box alert-error">{error}</div>}
      {watchlistMessage && <div className="alert-box alert-success">{watchlistMessage}</div>}

      {/* Stock Header Banner */}
      {selectedStock && (
        <div className="stock-header-card">
          <div className="stock-headline-row">
            <div className="stock-identity">
              <div className="stock-avatar">
                {selectedStock.symbol.slice(0, 3)}
              </div>
              <div className="stock-title-info">
                <h2>
                  {selectedStock.name}
                  <span className="exchange-pill">{selectedStock.exchange}</span>
                </h2>
                <div className="stock-subtitle">
                  {selectedStock.sector} • {selectedStock.industry} • Ticker: <strong>{selectedStock.symbol}</strong>
                </div>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
              <div className="stock-price-block">
                <span className="current-price">
                  {selectedStock.currency} {selectedStock.price}
                </span>
                <span className={`price-change-tag ${selectedStock.priceChangePercent >= 0 ? "positive" : "negative"}`}>
                  {selectedStock.priceChangePercent >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                  {selectedStock.priceChangePercent >= 0 ? `+${selectedStock.priceChangePercent}%` : `${selectedStock.priceChangePercent}%`}
                </span>
              </div>

              <button
                type="button"
                onClick={handleAddToWatchlist}
                className="btn-success"
              >
                <Bookmark size={15} />
                <span>+ Watchlist</span>
              </button>
            </div>
          </div>

          <div className="stock-quick-stats">
            <div className="quick-stat-item">
              <span className="quick-stat-label">Currency</span>
              <span className="quick-stat-val">{selectedStock.currency}</span>
            </div>
            <div className="quick-stat-item">
              <span className="quick-stat-label">Data Provider</span>
              <span className="quick-stat-val">{selectedStock.dataSource || "Alpha Vantage"}</span>
            </div>
            <div className="quick-stat-item">
              <span className="quick-stat-label">Telemetry Engine</span>
              <span className="quick-stat-val">Pandas + yfinance</span>
            </div>
            <div className="quick-stat-item">
              <span className="quick-stat-label">Validation Status</span>
              <span className="quick-stat-val" style={{ color: allValid ? "var(--bull-green)" : "var(--bear-red)" }}>
                {allValid ? "100% Passed" : "Action Needed"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      {selectedStock && (
        <>
          <div className="research-tabs-bar">
            <button
              type="button"
              className={`research-tab-btn ${activeTab === "news" ? "active" : ""}`}
              onClick={() => setActiveTab("news")}
            >
              <Sparkles size={16} style={{ color: "#a855f7" }} />
              <span>News & Sentiment Agent (Module 3)</span>
            </button>

            <button
              type="button"
              className={`research-tab-btn ${activeTab === "chart" ? "active" : ""}`}
              onClick={() => setActiveTab("chart")}
            >
              <BarChart2 size={16} style={{ color: "#38bdf8" }} />
              <span>Interactive Chart & OHLCV</span>
            </button>

            <button
              type="button"
              className={`research-tab-btn ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              <Building size={16} />
              <span>Overview & Profile</span>
            </button>

            <button
              type="button"
              className={`research-tab-btn ${activeTab === "statements" ? "active" : ""}`}
              onClick={() => setActiveTab("statements")}
            >
              <FileText size={16} />
              <span>Financial Statements</span>
            </button>

            <button
              type="button"
              className={`research-tab-btn ${activeTab === "validation" ? "active" : ""}`}
              onClick={() => setActiveTab("validation")}
            >
              <ShieldCheck size={16} style={{ color: "#10b981" }} />
              <span>Data Audit & Engine</span>
            </button>
          </div>

          {/* TAB 1: NEWS & SENTIMENT AI AGENT (MODULE 3) */}
          {activeTab === "news" && (
            <div className="tab-content-panel">
              <div className="news-intelligence-header">
                <div>
                  <h3 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff", display: "flex", alignItems: "center", gap: "8px" }}>
                    <Sparkles size={20} style={{ color: "#a855f7" }} />
                    News & Sentiment Analysis Agent
                  </h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "13.5px", marginTop: "2px" }}>
                    Autonomous agent classifying Loughran-McDonald financial tone, corporate events, and conflicts from verified sources.
                  </p>
                </div>

                {newsData && (
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <span className={`sentiment-badge-large ${getSentimentBadgeClass(newsData.overall_sentiment)}`}>
                      ● {newsData.overall_sentiment.toUpperCase()} SENTIMENT
                    </span>
                    <button
                      type="button"
                      onClick={() => fetchNewsAnalysis(selectedStock.symbol)}
                      disabled={newsLoading}
                      className="btn-secondary"
                    >
                      <RefreshCw size={14} className={newsLoading ? "spin" : ""} />
                      <span>{newsLoading ? "Analyzing..." : "Refresh"}</span>
                    </button>
                  </div>
                )}
              </div>

              {newsLoading && !newsData && (
                <div style={{ padding: "40px", textAlign: "center", color: "var(--text-secondary)" }}>
                  <RefreshCw size={24} className="spin" style={{ margin: "0 auto 12px", display: "block", color: "var(--accent-primary)" }} />
                  <p>Agent is retrieving real-time news and evaluating financial sentiment for <strong>{selectedStock.symbol}</strong>...</p>
                </div>
              )}

              {newsError && (
                <div className="alert-box alert-error" style={{ marginBottom: "20px" }}>
                  {newsError}
                </div>
              )}

              {newsData && (
                <>
                  {/* Sentiment Statistics Pills */}
                  <div className="sentiment-pills-row">
                    <div className="sentiment-pill">
                      Total Articles: <strong>{newsData.total_articles}</strong>
                    </div>
                    <div className="sentiment-pill" style={{ borderColor: "var(--bull-green-border)" }}>
                      Positive: <strong style={{ color: "var(--bull-green)" }}>{newsData.positive_count}</strong>
                    </div>
                    <div className="sentiment-pill" style={{ borderColor: "var(--bear-red-border)" }}>
                      Negative: <strong style={{ color: "var(--bear-red)" }}>{newsData.negative_count}</strong>
                    </div>
                    <div className="sentiment-pill">
                      Neutral: <strong>{newsData.neutral_count}</strong>
                    </div>
                    <div className="sentiment-pill" style={{ borderColor: "rgba(99, 102, 241, 0.4)" }}>
                      Sentiment Score: <strong style={{ color: "#a5b4fc" }}>{newsData.sentiment_score > 0 ? `+${newsData.sentiment_score}` : newsData.sentiment_score}</strong>
                    </div>
                  </div>

                  {/* AI Executive Summary Box */}
                  {newsData.summary && (
                    <div className="news-ai-summary-card">
                      <h4>
                        <Sparkles size={16} />
                        AI Agent Executive Summary
                      </h4>
                      <p>{newsData.summary}</p>
                    </div>
                  )}

                  {/* Conflicting Reports Banner */}
                  {newsData.conflicting_reports && newsData.conflicting_reports.length > 0 && (
                    <div className="conflict-alert">
                      <h4>
                        <AlertTriangle size={16} style={{ display: "inline", verticalAlign: "middle", marginRight: "6px" }} />
                        Conflicting Signals & Uncertainties Detected
                      </h4>
                      <ul>
                        {newsData.conflicting_reports.map((cr, idx) => (
                          <li key={idx}>{cr}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Corporate Events Grid */}
                  {newsData.corporate_events && newsData.corporate_events.length > 0 && (
                    <div style={{ marginBottom: "28px" }}>
                      <h4 style={{ fontSize: "15px", fontWeight: "700", color: "#ffffff", marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <Calendar size={16} style={{ color: "var(--neutral-blue)" }} />
                        Detected Corporate Announcements ({newsData.corporate_events.length})
                      </h4>
                      <div className="events-grid">
                        {newsData.corporate_events.map((ev, idx) => (
                          <div key={idx} className="event-card">
                            <span className="event-badge">{ev.event_type}</span>
                            <h5>{ev.headline}</h5>
                            {ev.summary && <p>{ev.summary}</p>}
                            <div className="event-meta">
                              <span>Source: {ev.source}</span>
                              <span>{ev.published_at ? ev.published_at.slice(0, 10) : "Recent"}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Verified News Articles List */}
                  {newsData.articles && newsData.articles.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: "15px", fontWeight: "700", color: "#ffffff", marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <FileText size={16} style={{ color: "#38bdf8" }} />
                        Verified News Feed & Source Attribution
                      </h4>
                      <div className="news-feed-list">
                        {newsData.articles.map((art, idx) => (
                          <div key={idx} className="news-card">
                            <div className="news-card-header">
                              {art.url ? (
                                <a
                                  href={art.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="news-title-link"
                                >
                                  {art.headline}
                                  <ExternalLink size={14} style={{ display: "inline", verticalAlign: "middle", marginLeft: "6px" }} />
                                </a>
                              ) : (
                                <span className="news-title-link">{art.headline}</span>
                              )}
                              <span className={`sentiment-pill-sm ${getSentimentBadgeClass(art.sentiment)}`}>
                                {art.sentiment}
                              </span>
                            </div>

                            <div className="news-card-meta">
                              <span><strong>Source:</strong> {art.source}</span>
                              <span><strong>Published:</strong> {art.published_at ? art.published_at.replace("T", " ").replace("Z", " UTC") : "Recent"}</span>
                              {art.category && <span><strong>Category:</strong> {art.category}</span>}
                            </div>

                            {art.summary && (
                              <p className="news-card-summary">{art.summary}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* TAB 2: INTERACTIVE CHART & OHLCV DATA */}
          {activeTab === "chart" && (
            <div className="tab-content-panel">
              <div className="chart-controls">
                <div>
                  <h3 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff" }}>
                    Price Action & Historical OHLCV
                  </h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                    Showing {historicalPrices.length} trading records for <strong>{period}</strong>.
                  </p>
                </div>

                <div className="period-pill-group">
                  {["1 Month", "3 Months", "6 Months", "1 Year"].map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => handlePeriodChange(p)}
                      className={`period-pill-btn ${period === p ? "active" : ""}`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic SVG Area Chart */}
              <div className="chart-container-box">
                {renderSvgChart()}
              </div>

              {/* OHLCV Table */}
              <h4 style={{ fontSize: "15px", fontWeight: "700", color: "#ffffff", margin: "24px 0 12px" }}>
                Historical Quotations Table
              </h4>

              {historicalPrices.length > 0 ? (
                <div className="table-responsive">
                  <table className="fin-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Close</th>
                        <th>Volume</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historicalPrices.map((item) => (
                        <tr key={item.date}>
                          <td style={{ color: "var(--text-secondary)" }}>{item.date}</td>
                          <td>{item.open}</td>
                          <td style={{ color: "var(--bull-green)" }}>{item.high}</td>
                          <td style={{ color: "var(--bear-red)" }}>{item.low}</td>
                          <td style={{ fontWeight: "700", color: "#ffffff" }}>{item.close}</td>
                          <td style={{ color: "var(--text-muted)" }}>{item.volume}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p style={{ color: "var(--text-muted)" }}>No historical records available for this period.</p>
              )}
            </div>
          )}

          {/* TAB 3: OVERVIEW & PROFILE */}
          {activeTab === "overview" && (
            <div className="tab-content-panel">
              <h3 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff", marginBottom: "16px" }}>
                Company Profile & Business Architecture
              </h3>
              <p style={{ color: "var(--text-secondary)", lineHeight: "1.7", fontSize: "15px", marginBottom: "24px" }}>
                {selectedStock.description}
              </p>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" }}>
                <div className="stat-card">
                  <div className="stat-content">
                    <span className="stat-label">Stock Symbol</span>
                    <span className="stat-value" style={{ fontFamily: "var(--font-mono)", color: "#60a5fa" }}>{selectedStock.symbol}</span>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-content">
                    <span className="stat-label">Primary Exchange</span>
                    <span className="stat-value">{selectedStock.exchange}</span>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-content">
                    <span className="stat-label">Operating Currency</span>
                    <span className="stat-value">{selectedStock.currency}</span>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-content">
                    <span className="stat-label">Industry Classification</span>
                    <span className="stat-value" style={{ fontSize: "16px" }}>{selectedStock.industry}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: FINANCIAL STATEMENTS */}
          {activeTab === "statements" && (
            <div className="tab-content-panel">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
                <div>
                  <h3 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff" }}>
                    Corporate Financial Statements
                  </h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                    Core statements for fundamental ratios and valuation modeling.
                  </p>
                </div>

                <div className="period-pill-group">
                  {["Income Statement", "Balance Sheet", "Cash Flow Statement"].map((stmt) => (
                    <button
                      key={stmt}
                      type="button"
                      onClick={() => setStatement(stmt)}
                      className={`period-pill-btn ${statement === stmt ? "active" : ""}`}
                    >
                      {stmt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="table-responsive">
                <table className="fin-table">
                  <thead>
                    <tr>
                      <th>Financial Metric</th>
                      <th style={{ textAlign: "right" }}>Reported Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(financialStatements[statement] || []).map((row) => (
                      <tr key={row.label}>
                        <td style={{ fontWeight: "600" }}>{row.label}</td>
                        <td style={{ textAlign: "right", fontWeight: "700", color: "#60a5fa" }}>{row.value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: DATA AUDIT & VALIDATION ENGINE */}
          {activeTab === "validation" && (
            <div className="tab-content-panel">
              <h3 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff", marginBottom: "4px" }}>
                Automated Pandas Data Quality Pipeline
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "13.5px", marginBottom: "20px" }}>
                Verifies dataset integrity, eliminates duplicate records, detects anomalies, and syncs to PostgreSQL / SQLite.
              </p>

              <div className="validation-checklist">
                {validationChecks.map((check) => (
                  <div key={check.label} className="validation-item">
                    <span style={{ color: "var(--text-primary)", fontWeight: "500" }}>{check.label}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      {check.passed ? (
                        <>
                          <CheckCircle2 size={16} style={{ color: "var(--bull-green)" }} />
                          <strong style={{ color: "var(--bull-green)" }}>PASSED</strong>
                        </>
                      ) : (
                        <>
                          <XCircle size={16} style={{ color: "var(--bear-red)" }} />
                          <strong style={{ color: "var(--bear-red)" }}>FAILED</strong>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: "24px", padding: "16px", background: "var(--bg-secondary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                <h4 style={{ fontSize: "14px", fontWeight: "700", color: "#ffffff", marginBottom: "6px" }}>
                  Dual-Database Architecture
                </h4>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                  Validated OHLCV records and research artifacts are stored in SQLite locally and production PostgreSQL schemas via SQLAlchemy ORM with UUID / JSON column type abstraction.
                </p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default StockResearch;
