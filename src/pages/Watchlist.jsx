import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
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
      setError(
        err.response?.data?.detail || "Unable to load your watchlist."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, []);

  const addStock = async () => {
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
      setError(
        err.response?.data?.detail || "Unable to add this stock."
      );
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
      setError(
        err.response?.data?.detail || "Unable to remove this stock."
      );
    }
  };

  return (
    <div className="watchlist-container">
      <button
        className="back-button"
        onClick={() => navigate("/dashboard")}
      >
        ← Back to Dashboard
      </button>

      <div className="watchlist-header">
        <h1>My Watchlist</h1>
        <p>Keep track of the stocks you are interested in (isolated to your account).</p>
      </div>

      <div className="watchlist-add">
        <h2>Add a Stock</h2>

        <div className="watchlist-input">
          <input
            type="text"
            value={symbol}
            onChange={(e) => {
              setSymbol(e.target.value);
              setError("");
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") addStock();
            }}
            placeholder="Enter stock symbol (e.g. INFY, TCS, RELIANCE)"
          />

          <button onClick={addStock} disabled={adding}>
            {adding ? "Adding..." : "Add Stock"}
          </button>
        </div>
      </div>

      {error && (
        <p className="watchlist-error">{error}</p>
      )}

      <div className="watchlist-content">
        <h2>Saved Stocks</h2>

        {loading ? (
          <p>Loading your watchlist...</p>
        ) : stocks.length === 0 ? (
          <p>Your watchlist is empty. Add a stock to get started.</p>
        ) : (
          <div className="watchlist-list">
            {stocks.map((stock) => (
              <div
                className="watchlist-item"
                key={stock.id}
                style={{ cursor: "pointer" }}
                onClick={() => navigate(`/stock-research?ticker=${encodeURIComponent(stock.symbol)}`)}
                title="Click to view full stock research"
              >
                <div>
                  <h3>{stock.symbol}</h3>
                  <p>{stock.company_name ? `${stock.company_name} • ` : ""}Click to analyze</p>
                </div>

                <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                  <button
                    style={{
                      padding: "8px 14px",
                      background: "#2563eb",
                      color: "#fff",
                      border: "none",
                      borderRadius: "7px",
                      cursor: "pointer",
                      fontSize: "13px"
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/stock-research?ticker=${encodeURIComponent(stock.symbol)}`);
                    }}
                  >
                    Analyze
                  </button>
                  <button
                    className="remove-button"
                    onClick={(e) => removeStock(stock.id, e)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}

export default Watchlist;
