import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import api from "../services/api";

function Dashboard() {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const initialTicker = searchParams.get("ticker") || "INFY";

  const [searchQuery, setSearchQuery] = useState(initialTicker);
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [period, setPeriod] = useState("3mo");
  const [loading, setLoading] = useState(false);
  const [watchlistMessage, setWatchlistMessage] = useState("");
  const [recentHistory, setRecentHistory] = useState([]);
  const navigate = useNavigate();

  // Load default or query-param stock and research history on mount
  useEffect(() => {
    loadStockData(initialTicker, period);
    fetchResearchHistory();
  }, [initialTicker]);

  const fetchResearchHistory = async () => {
    try {
      const res = await api.get("/research-history?limit=6");
      setRecentHistory(res.data || []);
    } catch (err) {
      console.log("Could not load recent history:", err);
    }
  };

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (!query || query.trim().length < 1) {
      setSearchResults([]);
      return;
    }
    try {
      const res = await api.get(`/stocks/search?query=${encodeURIComponent(query)}`);
      setSearchResults(res.data || []);
    } catch (err) {
      console.error("Search error:", err);
    }
  };

  const loadStockData = async (ticker, selectedPeriod = period) => {
    if (!ticker || !ticker.trim()) return;
    setLoading(true);
    setWatchlistMessage("");
    setSearchResults([]);
    const cleanTicker = ticker.trim().toUpperCase();

    try {
      const res = await api.get(`/stocks/${encodeURIComponent(cleanTicker)}?period=${selectedPeriod}`);
      setSelectedStock(res.data);
      setSearchQuery(cleanTicker);

      // Explicitly record research activity to update user's research history
      try {
        await api.post("/research-history", {
          ticker_symbol: cleanTicker,
          company_name: res.data.metadata?.name || cleanTicker,
          analysis_period: selectedPeriod,
          research_summary: {
            price: res.data.metadata?.current_price,
            change_percent: res.data.metadata?.price_change_percent,
            source: res.data.metadata?.data_source
          }
        });
        // Refresh recent history view
        fetchResearchHistory();
      } catch (logErr) {
        console.log("Research history log note:", logErr);
      }
    } catch (err) {
      console.error("Failed to load stock data:", err);
      alert(err.response?.data?.detail || `Failed to fetch data for ${cleanTicker}`);
    } finally {
      setLoading(false);
    }
  };

  const addToWatchlist = async () => {
    if (!selectedStock) return;
    try {
      await api.post("/watchlist", {
        symbol: selectedStock.ticker,
        company_name: selectedStock.metadata?.name || selectedStock.ticker,
        exchange: selectedStock.metadata?.exchange || "NSE"
      });
      setWatchlistMessage(`✅ ${selectedStock.ticker} added to your watchlist!`);
    } catch (err) {
      setWatchlistMessage(err.response?.data?.detail || "Could not add to watchlist");
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem("token");
    navigate("/login");
  };

  // Helper to render interactive SVG chart
  const renderPriceChart = (history) => {
    if (!history || history.length < 2) return null;
    const prices = history.map((h) => h.close);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const range = maxPrice - minPrice || 1;

    const width = 800;
    const height = 240;
    const padding = 30;

    const points = prices.map((price, idx) => {
      const x = padding + (idx / (prices.length - 1)) * (width - 2 * padding);
      const y = height - padding - ((price - minPrice) / range) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(" ");

    const firstPoint = `${padding},${height - padding}`;
    const lastPoint = `${width - padding},${height - padding}`;
    const fillArea = `${points} L ${lastPoint} L ${firstPoint} Z`;

    const isPositive = prices[prices.length - 1] >= prices[0];
    const strokeColor = isPositive ? "#10b981" : "#ef4444";
    const fillColor = isPositive ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)";

    return (
      <div style={{ background: "#1f2937", padding: "16px", borderRadius: "10px", marginTop: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "14px", color: "#9ca3af" }}>
          <span>Price Trend ({history.length} Validated Daily Points)</span>
          <span>Range: {selectedStock?.metadata?.currency || "$"} {minPrice.toFixed(2)} - {maxPrice.toFixed(2)}</span>
        </div>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "240px", overflow: "visible" }}>
          <polygon points={fillArea} fill={fillColor} />
          <polyline fill="none" stroke={strokeColor} strokeWidth="2.5" points={points} />
        </svg>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px", fontSize: "12px", color: "#6b7280" }}>
          <span>{history[0]?.date}</span>
          <span>{history[Math.floor(history.length / 2)]?.date}</span>
          <span>{history[history.length - 1]?.date}</span>
        </div>
      </div>
    );
  };

  const meta = selectedStock?.metadata;
  const report = selectedStock?.validation_report;
  const history = selectedStock?.historical_data || [];

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "24px 16px", fontFamily: "sans-serif", textAlign: "left" }}>
      {/* Top Header */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #374151", paddingBottom: "16px", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "28px", margin: 0, color: "#f3f4f6" }}>Market Research AI</h1>
          <p style={{ margin: "4px 0 0", color: "#9ca3af", fontSize: "14px" }}>Module 1 & 2: User Workspace, Stock Search & Live Data</p>
        </div>
        <nav style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <Link to="/watchlist" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "14px", padding: "6px 12px", background: "#1e293b", borderRadius: "6px" }}>Watchlist</Link>
          <Link to="/preferences" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "14px", padding: "6px 12px", background: "#1e293b", borderRadius: "6px" }}>Preferences</Link>
          <Link to="/research-history" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "14px", padding: "6px 12px", background: "#1e293b", borderRadius: "6px" }}>History ({recentHistory.length})</Link>
          <button onClick={handleLogout} style={{ background: "#ef4444", color: "#fff", border: "none", padding: "6px 12px", borderRadius: "6px", cursor: "pointer", fontSize: "14px" }}>Logout</button>
        </nav>
      </header>

      {/* Stock Search Bar */}
      <section style={{ marginBottom: "24px", position: "relative" }}>
        <div style={{ display: "flex", gap: "10px" }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search company by name or ticker (e.g. INFY, TCS, RELIANCE)..."
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: "8px",
              border: "1px solid #4b5563",
              background: "#111827",
              color: "#fff",
              fontSize: "16px"
            }}
          />
          <button
            onClick={() => loadStockData(searchQuery)}
            disabled={loading}
            style={{
              padding: "12px 24px",
              background: "#3b82f6",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              fontSize: "15px",
              fontWeight: 600,
              cursor: "pointer"
            }}
          >
            {loading ? "Analyzing..." : "Analyze Stock"}
          </button>
        </div>

        {/* Quick Ticker Chips */}
        <div style={{ display: "flex", gap: "8px", marginTop: "10px", alignItems: "center" }}>
          <span style={{ fontSize: "13px", color: "#9ca3af" }}>Quick Tickers:</span>
          {["INFY", "INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "TATAMOTORS.NS"].map((t) => (
            <button
              key={t}
              onClick={() => loadStockData(t)}
              style={{
                background: searchQuery === t ? "#2563eb" : "#374151",
                color: "#f3f4f6",
                border: "none",
                borderRadius: "14px",
                padding: "4px 10px",
                fontSize: "12px",
                cursor: "pointer"
              }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Autocomplete Dropdown */}
        {searchResults.length > 0 && (
          <ul style={{
            position: "absolute",
            top: "52px",
            left: 0,
            right: 0,
            zIndex: 50,
            background: "#1f2937",
            border: "1px solid #4b5563",
            borderRadius: "8px",
            listStyle: "none",
            margin: 0,
            padding: 0,
            maxHeight: "260px",
            overflowY: "auto",
            boxShadow: "0 10px 25px rgba(0,0,0,0.5)"
          }}>
            {searchResults.map((s) => (
              <li
                key={s.ticker}
                onClick={() => loadStockData(s.ticker)}
                style={{
                  padding: "10px 16px",
                  borderBottom: "1px solid #374151",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between"
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#374151")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "#1f2937")}
              >
                <div>
                  <strong style={{ color: "#60a5fa" }}>{s.ticker}</strong> &mdash; <span style={{ color: "#d1d5db" }}>{s.name}</span>
                </div>
                <span style={{ fontSize: "12px", color: "#9ca3af" }}>{s.region} ({s.currency})</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Recent Research History Quick Access Bar */}
      {recentHistory.length > 0 && (
        <section style={{ marginBottom: "20px", padding: "12px 16px", background: "#111827", border: "1px solid #374151", borderRadius: "8px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "#9ca3af" }}>🕒 Your Recent Research History:</span>
            <Link to="/research-history" style={{ fontSize: "12px", color: "#60a5fa", textDecoration: "none" }}>View All &rarr;</Link>
          </div>
          <div style={{ display: "flex", gap: "8px", overflowX: "auto", paddingBottom: "4px" }}>
            {recentHistory.map((item) => (
              <button
                key={item.id}
                onClick={() => loadStockData(item.stock_symbol || item.ticker_symbol)}
                style={{
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  padding: "6px 12px",
                  color: "#f1f5f9",
                  fontSize: "12px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  whiteSpace: "nowrap"
                }}
                title={`Researched at: ${item.created_at}`}
              >
                <strong style={{ color: "#38bdf8" }}>{item.stock_symbol || item.ticker_symbol}</strong>
                <span style={{ color: "#94a3b8", fontSize: "11px" }}>{item.company_name?.slice(0, 15)}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Selected Stock Overview Card */}
      {selectedStock && meta && (
        <section style={{ background: "#111827", border: "1px solid #374151", borderRadius: "12px", padding: "24px", marginBottom: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <h2 style={{ fontSize: "28px", margin: 0, color: "#f9fafb" }}>{meta.name || meta.ticker}</h2>
                <span style={{ background: "#1e3a8a", color: "#bfdbfe", padding: "3px 8px", borderRadius: "6px", fontSize: "12px", fontWeight: 600 }}>
                  {meta.ticker} ({meta.exchange || "GLOBAL"})
                </span>
              </div>
              <p style={{ color: "#9ca3af", marginTop: "4px", fontSize: "14px" }}>
                Sector: {meta.sector || "Information Technology"} | Currency: {meta.currency || "USD"}
              </p>
            </div>

            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "32px", fontWeight: "bold", color: "#f9fafb" }}>
                {meta.currency === "INR" ? "₹" : "$"}{meta.current_price?.toFixed(2)}
              </div>
              <div style={{ fontSize: "16px", fontWeight: 600, color: (meta.price_change || 0) >= 0 ? "#10b981" : "#ef4444" }}>
                {(meta.price_change || 0) >= 0 ? "▲ +" : "▼ "}
                {meta.price_change?.toFixed(2)} ({meta.price_change_percent?.toFixed(2)}%)
              </div>
            </div>
          </div>

          {/* Data Source & Pandas Validation Badges */}
          <div style={{ display: "flex", gap: "12px", marginTop: "16px", flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ background: "#065f46", color: "#a7f3d0", padding: "4px 10px", borderRadius: "6px", fontSize: "12px" }}>
              📡 Source: {meta.data_source}
            </span>
            <span style={{ background: "#312e81", color: "#c7d2fe", padding: "4px 10px", borderRadius: "6px", fontSize: "12px" }}>
              📊 Pandas Validation: {report?.status} ({report?.valid_records} valid OHLCV rows)
            </span>
            <span style={{ background: "#1f2937", color: "#9ca3af", padding: "4px 10px", borderRadius: "6px", fontSize: "12px" }}>
              🕒 Last Synced: {new Date(meta.retrieved_at).toLocaleTimeString()}
            </span>
            <button
              onClick={addToWatchlist}
              style={{
                marginLeft: "auto",
                background: "#0284c7",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                padding: "6px 14px",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer"
              }}
            >
              ⭐ Add to Watchlist
            </button>
          </div>

          {watchlistMessage && (
            <p style={{ marginTop: "10px", fontSize: "13px", color: watchlistMessage.includes("✅") ? "#34d399" : "#f87171" }}>
              {watchlistMessage}
            </p>
          )}

          {/* Financial Highlights */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", marginTop: "20px", borderTop: "1px solid #374151", paddingTop: "16px" }}>
            <div>
              <span style={{ color: "#9ca3af", fontSize: "12px" }}>Market Cap</span>
              <p style={{ fontSize: "16px", fontWeight: 600, color: "#f3f4f6" }}>
                {meta.market_cap ? (meta.market_cap / 1e9).toFixed(2) + "B" : "N/A"}
              </p>
            </div>
            <div>
              <span style={{ color: "#9ca3af", fontSize: "12px" }}>P/E Ratio</span>
              <p style={{ fontSize: "16px", fontWeight: 600, color: "#f3f4f6" }}>
                {meta.pe_ratio ? meta.pe_ratio.toFixed(2) : "N/A"}
              </p>
            </div>
            <div>
              <span style={{ color: "#9ca3af", fontSize: "12px" }}>52-Week High</span>
              <p style={{ fontSize: "16px", fontWeight: 600, color: "#10b981" }}>
                {meta.fifty_two_week_high ? (meta.currency === "INR" ? "₹" : "$") + meta.fifty_two_week_high.toFixed(2) : "N/A"}
              </p>
            </div>
            <div>
              <span style={{ color: "#9ca3af", fontSize: "12px" }}>52-Week Low</span>
              <p style={{ fontSize: "16px", fontWeight: 600, color: "#ef4444" }}>
                {meta.fifty_two_week_low ? (meta.currency === "INR" ? "₹" : "$") + meta.fifty_two_week_low.toFixed(2) : "N/A"}
              </p>
            </div>
          </div>

          {/* Timeframe selector & Chart */}
          <div style={{ marginTop: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0, fontSize: "18px", color: "#f3f4f6" }}>Historical Price Chart</h3>
              <div style={{ display: "flex", gap: "6px" }}>
                {["1mo", "3mo", "6mo", "1y"].map((p) => (
                  <button
                    key={p}
                    onClick={() => {
                      setPeriod(p);
                      loadStockData(meta.ticker, p);
                    }}
                    style={{
                      background: period === p ? "#3b82f6" : "#374151",
                      color: "#fff",
                      border: "none",
                      padding: "4px 10px",
                      borderRadius: "6px",
                      fontSize: "12px",
                      cursor: "pointer"
                    }}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
            {renderPriceChart(history)}
          </div>

          {/* Pandas Validated Historical Table */}
          <div style={{ marginTop: "24px" }}>
            <h3 style={{ fontSize: "18px", color: "#f3f4f6", marginBottom: "12px" }}>
              Validated OHLCV Data (PostgreSQL Synced)
            </h3>
            <div style={{ maxHeight: "260px", overflowY: "auto", border: "1px solid #374151", borderRadius: "8px" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
                <thead style={{ background: "#1f2937", position: "sticky", top: 0 }}>
                  <tr style={{ color: "#9ca3af", borderBottom: "1px solid #374151" }}>
                    <th style={{ padding: "8px 12px" }}>Date</th>
                    <th style={{ padding: "8px 12px" }}>Open</th>
                    <th style={{ padding: "8px 12px" }}>High</th>
                    <th style={{ padding: "8px 12px" }}>Low</th>
                    <th style={{ padding: "8px 12px" }}>Close</th>
                    <th style={{ padding: "8px 12px" }}>Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(-15).reverse().map((row, i) => (
                    <tr key={row.date} style={{ borderBottom: "1px solid #2d3748", background: i % 2 === 0 ? "#111827" : "#1a202c" }}>
                      <td style={{ padding: "8px 12px", color: "#d1d5db" }}>{row.date}</td>
                      <td style={{ padding: "8px 12px", color: "#d1d5db" }}>{row.open.toFixed(2)}</td>
                      <td style={{ padding: "8px 12px", color: "#34d399" }}>{row.high.toFixed(2)}</td>
                      <td style={{ padding: "8px 12px", color: "#f87171" }}>{row.low.toFixed(2)}</td>
                      <td style={{ padding: "8px 12px", fontWeight: 600, color: "#f3f4f6" }}>{row.close.toFixed(2)}</td>
                      <td style={{ padding: "8px 12px", color: "#9ca3af" }}>{row.volume.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

export default Dashboard;
