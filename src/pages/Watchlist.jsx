
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
      setStocks(response.data);
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

  const removeStock = async (id) => {
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
        <p>Keep track of the stocks you are interested in.</p>
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
            placeholder="Enter stock symbol (e.g. INFY)"
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
              <div className="watchlist-item" key={stock.id}>
                <div>
                  <h3>{stock.symbol}</h3>
                  <p>Stock Symbol</p>
                </div>

                <button
                  className="remove-button"
                  onClick={() => removeStock(stock.id)}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}

export default Watchlist;
