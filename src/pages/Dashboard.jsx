import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

function Dashboard() {
  const navigate = useNavigate();
  const [quickSearch, setQuickSearch] = useState("");
  const [recentHistory, setRecentHistory] = useState([]);
  const [watchlistCount, setWatchlistCount] = useState(0);

  useEffect(() => {
    // Load summary info
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

  const handleLogout = () => {
    sessionStorage.removeItem("token");
    navigate("/login");
  };

  const handleQuickSearchSubmit = (e) => {
    e.preventDefault();
    if (quickSearch.trim()) {
      navigate(`/stock-research?ticker=${encodeURIComponent(quickSearch.trim().toUpperCase())}`);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Welcome to Market Research AI</h1>
          <p>Your personal multi-agent stock research workspace</p>
        </div>

        <button onClick={handleLogout} className="back-button" style={{ background: "#fee2e2", color: "#991b1b", border: "1px solid #f87171" }}>
          Logout
        </button>
      </div>

      {/* Quick Search Bar */}
      <div style={{ background: "#ffffff", padding: "20px 25px", borderRadius: "14px", border: "1px solid #e2e8f0", marginBottom: "25px", boxShadow: "0 2px 8px rgba(15,23,42,0.04)" }}>
        <h3 style={{ margin: "0 0 10px", color: "#1e3a8a", fontSize: "18px" }}>Quick Stock Analysis</h3>
        <form onSubmit={handleQuickSearchSubmit} style={{ display: "flex", gap: "12px" }}>
          <input
            type="text"
            placeholder="Enter stock symbol (e.g. INFY, TCS, RELIANCE, AAPL, IBM)..."
            value={quickSearch}
            onChange={(e) => setQuickSearch(e.target.value)}
            style={{ flex: 1, padding: "12px 16px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "15px" }}
          />
          <button
            type="submit"
            style={{ padding: "12px 24px", background: "#2563eb", color: "#ffffff", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "600", fontSize: "14px" }}
          >
            Research Stock &rarr;
          </button>
        </form>
      </div>

      <div className="dashboard-cards">
        <Link to="/stock-research" className="dashboard-card">
          <h3>Stock Research</h3>
          <p>Search stocks and explore live prices, historical OHLCV data, Pandas validation, and financial statements.</p>
        </Link>

        <Link to="/research-history" className="dashboard-card">
          <h3>Research History</h3>
          <p>
            View your previous research activities.
            {recentHistory.length > 0 && ` (${recentHistory.length} recorded recently)`}
          </p>
        </Link>

        <Link to="/watchlist" className="dashboard-card">
          <h3>My Watchlist</h3>
          <p>
            Keep track of your selected stocks.
            {watchlistCount > 0 ? ` (${watchlistCount} stocks saved)` : " (0 stocks saved)"}
          </p>
        </Link>

        <Link to="/preferences" className="dashboard-card">
          <h3>Preferences</h3>
          <p>Manage your default market (NSE, BSE, NASDAQ, NYSE) and research analysis periods.</p>
        </Link>
      </div>

      {/* Recent Activity Snapshot */}
      {recentHistory.length > 0 && (
        <div style={{ marginTop: "30px", background: "#ffffff", padding: "20px 25px", borderRadius: "14px", border: "1px solid #e2e8f0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
            <h3 style={{ margin: 0, color: "#1e293b", fontSize: "18px" }}>Recent Research Activity</h3>
            <Link to="/research-history" style={{ color: "#2563eb", fontSize: "13px", fontWeight: "600", textDecoration: "none" }}>
              View All History &rarr;
            </Link>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "12px" }}>
            {recentHistory.map((item) => (
              <div
                key={item.id}
                onClick={() => navigate(`/stock-research?ticker=${encodeURIComponent(item.stock_symbol || item.ticker_symbol)}`)}
                style={{
                  padding: "14px",
                  background: "#f8fafc",
                  borderRadius: "8px",
                  border: "1px solid #e2e8f0",
                  cursor: "pointer",
                  transition: "border-color 0.2s"
                }}
              >
                <div style={{ fontWeight: "bold", color: "#2563eb", fontSize: "16px" }}>
                  {item.stock_symbol || item.ticker_symbol}
                </div>
                <div style={{ fontSize: "13px", color: "#475569", marginTop: "4px" }}>
                  {item.company_name}
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "6px" }}>
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
