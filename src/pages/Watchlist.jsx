import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bookmark,
  Plus,
  Trash2,
  TrendingUp,
  Search,
  ExternalLink,
  ArrowRight
} from "lucide-react";
import api from "../services/api";

function Watchlist() {
  const navigate = useNavigate();

  const [stocks, setStocks] = useState([]);
  const [symbol, setSymbol] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  const fetchStocks = async () => {
    try {
      setLoading(true);
      setError("");
      const response = await api.get("/watchlist");
      setStocks(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load your watchlist.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, []);

  const addStock = async (e) => {
    if (e) e.preventDefault();
    const stockSymbol = symbol.trim().toUpperCase();

    if (!stockSymbol) {
      setError("Please enter a stock symbol.");
      return;
    }

    try {
      setAdding(true);
      setError("");

      await api.post("/watchlist", {
        symbol: stockSymbol
      });

      setSymbol("");
      await fetchStocks();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to add this stock to your watchlist.");
    } finally {
      setAdding(false);
    }
  };

  const removeStock = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      setError("");
      await api.delete(`/watchlist/${id}`);
      await fetchStocks();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to remove this stock.");
    }
  };

  const handleOpenResearch = (stockSymbol) => {
    navigate(`/stock-research?ticker=${encodeURIComponent(stockSymbol)}`);
  };

  return (
    <div className="watchlist-page">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "26px", fontWeight: "800", color: "#ffffff", letterSpacing: "-0.4px" }}>
            My Watchlist
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "4px" }}>
            Track and quickly access live intelligence for your favorite equities.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="back-button"
        >
          &larr; Back to Dashboard
        </button>
      </div>

      {/* Add Stock Card */}
      <div className="tab-content-panel" style={{ marginBottom: "26px" }}>
        <h3 style={{ fontSize: "16px", fontWeight: "700", color: "#ffffff", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
          <Plus size={18} style={{ color: "var(--neutral-blue)" }} />
          Add Symbol to Watchlist
        </h3>

        <form onSubmit={addStock} style={{ display: "flex", gap: "12px", maxWidth: "600px" }}>
          <input
            type="text"
            placeholder="Enter symbol (e.g. INFY, TCS, RELIANCE, AAPL)..."
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            style={{
              flex: 1,
              padding: "12px 16px",
              background: "var(--bg-secondary)",
              border: "1px solid var(--border-light)",
              borderRadius: "var(--radius-md)",
              color: "#ffffff",
              fontSize: "14px",
              outline: "none"
            }}
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={adding}
          >
            {adding ? "Adding..." : "+ Add Stock"}
          </button>
        </form>

        {error && (
          <div className="alert-box alert-error" style={{ marginTop: "14px" }}>
            {error}
          </div>
        )}
      </div>

      {/* Watchlist Items */}
      <div className="tab-content-panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ fontSize: "16px", fontWeight: "700", color: "#ffffff", display: "flex", alignItems: "center", gap: "8px" }}>
            <Bookmark size={18} style={{ color: "var(--bull-green)" }} />
            Monitored Stocks ({stocks.length})
          </h3>
        </div>

        {loading ? (
          <p style={{ color: "var(--text-muted)", padding: "20px 0" }}>Loading your watchlist...</p>
        ) : stocks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px 20px", color: "var(--text-secondary)" }}>
            <Bookmark size={36} style={{ color: "var(--text-muted)", marginBottom: "12px" }} />
            <h4 style={{ color: "#ffffff", fontSize: "16px", marginBottom: "6px" }}>Your Watchlist is Empty</h4>
            <p style={{ fontSize: "13.5px", maxWidth: "380px", margin: "0 auto" }}>
              Add stock symbols like INFY, TCS, RELIANCE, or AAPL using the form above to monitor them in one place.
            </p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="fin-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Company Name</th>
                  <th>Exchange</th>
                  <th>Added On</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {stocks.map((stock) => (
                  <tr key={stock.id}>
                    <td>
                      <span style={{ fontWeight: "800", color: "#60a5fa", fontFamily: "var(--font-mono)", fontSize: "15px" }}>
                        {stock.stock_symbol || stock.symbol}
                      </span>
                    </td>
                    <td>{stock.company_name || stock.symbol}</td>
                    <td>
                      <span className="exchange-pill">
                        {stock.exchange || "NSE"}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-muted)", fontSize: "12px" }}>
                      {stock.created_at ? new Date(stock.created_at).toLocaleDateString() : "Recent"}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: "8px" }}>
                        <button
                          type="button"
                          onClick={() => handleOpenResearch(stock.stock_symbol || stock.symbol)}
                          className="btn-secondary"
                          style={{ padding: "6px 12px", fontSize: "12px" }}
                        >
                          <span>Analyze</span>
                          <ArrowRight size={13} />
                        </button>
                        <button
                          type="button"
                          onClick={(e) => removeStock(stock.id, e)}
                          className="btn-danger"
                          style={{ padding: "6px 10px" }}
                          title="Remove from Watchlist"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Watchlist;
