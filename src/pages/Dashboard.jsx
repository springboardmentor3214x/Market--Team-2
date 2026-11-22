import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Search,
  Bookmark,
  Clock,
  Settings,
  Sparkles,
  TrendingUp,
  BarChart2,
  ArrowRight,
  ShieldCheck,
  Globe,
  Layers,
  Cpu
} from "lucide-react";
import api from "../services/api";

function Dashboard() {
  const navigate = useNavigate();
  const [quickSearch, setQuickSearch] = useState("");
  const [recentHistory, setRecentHistory] = useState([]);
  const [watchlistCount, setWatchlistCount] = useState(0);

  const popularTickers = ["INFY", "TCS", "RELIANCE", "AAPL", "MSFT", "NVDA"];

  useEffect(() => {
    const loadOverview = async () => {
      try {
        const histRes = await api.get("/research-history?limit=4");
        setRecentHistory(histRes.data || []);
      } catch (err) {
        console.log("History overview note:", err);
      }

      try {
        const wlRes = await api.get("/watchlist");
        setWatchlistCount(wlRes.data?.length || 0);
      } catch (err) {
        console.log("Watchlist overview note:", err);
      }
    };

    loadOverview();
  }, []);

  const handleQuickSearchSubmit = (e) => {
    e.preventDefault();
    if (quickSearch.trim()) {
      navigate(`/stock-research?ticker=${encodeURIComponent(quickSearch.trim().toUpperCase())}`);
    }
  };

  const handleChipClick = (ticker) => {
    navigate(`/stock-research?ticker=${encodeURIComponent(ticker)}`);
  };

  return (
    <div className="dashboard-page">
      {/* Hero Section */}
      <div className="dashboard-hero">
        <div className="hero-tag">
          <Sparkles size={12} />
          <span>Module 3 Multi-Agent Intelligence Active</span>
        </div>

        <h1>Stock Research & Financial Intelligence</h1>
        <p>
          Analyze equities with specialized AI agents for real-time news sentiment,
          fundamental metrics, technical trends, and risk assessment.
        </p>

        {/* Quick Search */}
        <form onSubmit={handleQuickSearchSubmit} className="hero-search-form">
          <div className="search-input-wrapper">
            <Search size={18} className="search-icon-inside" />
            <input
              type="text"
              placeholder="Search company or ticker (e.g. INFY, TCS, RELIANCE, AAPL)..."
              value={quickSearch}
              onChange={(e) => setQuickSearch(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary">
            Analyze Stock <ArrowRight size={16} />
          </button>
        </form>

        {/* Quick Ticker Chips */}
        <div className="quick-chips-row">
          <span className="quick-chips-label">Popular:</span>
          {popularTickers.map((ticker) => (
            <button
              key={ticker}
              type="button"
              onClick={() => handleChipClick(ticker)}
              className="ticker-chip"
            >
              {ticker}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ background: "rgba(16, 185, 129, 0.15)", color: "#10b981" }}>
            <Bookmark size={22} />
          </div>
          <div className="stat-content">
            <span className="stat-label">Watchlist Stocks</span>
            <span className="stat-value">{watchlistCount}</span>
            <span className="stat-subtext">Monitored equities</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ background: "rgba(37, 99, 235, 0.15)", color: "#3b82f6" }}>
            <Clock size={22} />
          </div>
          <div className="stat-content">
            <span className="stat-label">Recent Researches</span>
            <span className="stat-value">{recentHistory.length}</span>
            <span className="stat-subtext">Session queries</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ background: "rgba(99, 102, 241, 0.15)", color: "#818cf8" }}>
            <Cpu size={22} />
          </div>
          <div className="stat-content">
            <span className="stat-label">AI Agents</span>
            <span className="stat-value">4 Online</span>
            <span className="stat-subtext">News, Fund, Tech, Risk</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper" style={{ background: "rgba(6, 182, 212, 0.15)", color: "#06b6d4" }}>
            <Globe size={22} />
          </div>
          <div className="stat-content">
            <span className="stat-label">Markets Covered</span>
            <span className="stat-value">NSE / US</span>
            <span className="stat-subtext">NSE, BSE, NASDAQ, NYSE</span>
          </div>
        </div>
      </div>

      {/* Navigation Modules */}
      <div className="modules-grid">
        <Link to="/stock-research" className="module-card">
          <div className="module-card-header">
            <div className="module-icon-box">
              <BarChart2 size={22} />
            </div>
            <ArrowRight size={18} style={{ color: "var(--text-muted)" }} />
          </div>
          <h3>Stock Research & News Agent</h3>
          <p>
            Dive into live OHLCV candlestick data, Loughran-McDonald news sentiment, corporate event detection, and clean Pandas reports.
          </p>
          <div className="module-card-footer">
            <span>Explore Workspace</span>
            <ArrowRight size={14} />
          </div>
        </Link>

        <Link to="/watchlist" className="module-card">
          <div className="module-card-header">
            <div className="module-icon-box" style={{ color: "#10b981" }}>
              <Bookmark size={22} />
            </div>
            <ArrowRight size={18} style={{ color: "var(--text-muted)" }} />
          </div>
          <h3>Personal Watchlist</h3>
          <p>
            Curate and manage your custom portfolio of tracked equities with 1-click instant analysis and isolated account storage.
          </p>
          <div className="module-card-footer" style={{ color: "#10b981" }}>
            <span>Manage Watchlist</span>
            <ArrowRight size={14} />
          </div>
        </Link>

        <Link to="/research-history" className="module-card">
          <div className="module-card-header">
            <div className="module-icon-box" style={{ color: "#f59e0b" }}>
              <Clock size={22} />
            </div>
            <ArrowRight size={18} style={{ color: "var(--text-muted)" }} />
          </div>
          <h3>Research History</h3>
          <p>
            Review audit logs of all past company inquiries, prices at query time, and quick links to refresh previous analyses.
          </p>
          <div className="module-card-footer" style={{ color: "#f59e0b" }}>
            <span>View History</span>
            <ArrowRight size={14} />
          </div>
        </Link>

        <Link to="/preferences" className="module-card">
          <div className="module-card-header">
            <div className="module-icon-box" style={{ color: "#a855f7" }}>
              <Settings size={22} />
            </div>
            <ArrowRight size={18} style={{ color: "var(--text-muted)" }} />
          </div>
          <h3>User Preferences</h3>
          <p>
            Configure default market exchanges (NSE, BSE, NASDAQ, NYSE), standard analysis windows (1M, 3M, 6M, 1Y), and UI preferences.
          </p>
          <div className="module-card-footer" style={{ color: "#a855f7" }}>
            <span>Configure Settings</span>
            <ArrowRight size={14} />
          </div>
        </Link>
      </div>

      {/* Recent Research Snapshot */}
      {recentHistory.length > 0 && (
        <div className="tab-content-panel" style={{ marginTop: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Clock size={18} style={{ color: "var(--neutral-blue)" }} />
              <h3 style={{ fontSize: "16px", fontWeight: "700", color: "#ffffff" }}>
                Recent Research Inquiries
              </h3>
            </div>
            <Link to="/research-history" style={{ fontSize: "13px", fontWeight: "600", color: "var(--neutral-blue)" }}>
              View Complete History &rarr;
            </Link>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "12px" }}>
            {recentHistory.map((item) => (
              <div
                key={item.id}
                onClick={() => navigate(`/stock-research?ticker=${encodeURIComponent(item.stock_symbol || item.ticker_symbol)}`)}
                style={{
                  padding: "14px",
                  background: "var(--bg-secondary)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-subtle)",
                  cursor: "pointer",
                  transition: "all var(--transition-fast)"
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--border-focus)";
                  e.currentTarget.style.transform = "translateY(-2px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border-subtle)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: "800", color: "#60a5fa", fontFamily: "var(--font-mono)", fontSize: "15px" }}>
                    {item.stock_symbol || item.ticker_symbol}
                  </span>
                  <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                    {item.analysis_period || "3mo"}
                  </span>
                </div>
                <div style={{ fontSize: "12.5px", color: "var(--text-secondary)", marginTop: "4px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {item.company_name}
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "8px" }}>
                  {item.created_at ? new Date(item.created_at).toLocaleDateString() : "Recent"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
