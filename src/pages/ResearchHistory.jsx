import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function ResearchHistory() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const fetchHistory = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/research-history");
      setHistory(response.data || []);
    } catch (err) {
      console.error("Error fetching research history:", err);
      setError("Unable to load research history. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/research-history/${id}`);
      setHistory(history.filter((item) => item.id !== id));
      setMessage("Item removed from history.");
      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      console.error("Delete history error:", err);
      alert("Could not delete history record");
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm("Are you sure you want to clear your entire research history?")) return;
    try {
      await api.delete("/research-history");
      setHistory([]);
      setMessage("All research history cleared.");
      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      console.error("Clear all error:", err);
      alert("Could not clear history");
    }
  };

  const handleOpenStock = (ticker) => {
    if (!ticker) return;
    navigate(`/stock-research?ticker=${encodeURIComponent(ticker)}`);
  };

  return (
    <div className="history-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <button
          className="back-button"
          onClick={() => navigate("/dashboard")}
        >
          ← Back to Dashboard
        </button>

        {history.length > 0 && (
          <button
            onClick={handleClearAll}
            style={{
              background: "#ef4444",
              color: "#ffffff",
              border: "none",
              padding: "8px 16px",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "13px"
            }}
          >
            Clear All History
          </button>
        )}
      </div>

      <div className="history-header">
        <h1>Research History</h1>
        <p>Track and revisit your past stock analysis activities (Isolated per user account).</p>
      </div>

      {message && (
        <div style={{ marginBottom: "16px", padding: "10px 14px", background: "#1e293b", border: "1px solid #3b82f6", borderRadius: "8px", color: "#93c5fd", fontSize: "14px" }}>
          {message}
        </div>
      )}

      <div className="history-content">
        {loading ? (
          <p className="history-message">Loading research history...</p>
        ) : error ? (
          <p className="history-error">{error}</p>
        ) : history.length === 0 ? (
          <div className="history-empty">
            <h3>No Research History Yet</h3>
            <p>Your researched companies will appear here whenever you search stocks.</p>
            <button onClick={() => navigate("/stock-research")}>
              Start Researching
            </button>
          </div>
        ) : (
          <div className="history-list">
            {history.map((item) => {
              const symbol = item.stock_symbol || item.ticker_symbol || "UNKNOWN";
              return (
                <div
                  className="history-item"
                  key={item.id}
                  onClick={() => handleOpenStock(symbol)}
                  style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}
                  title="Click to view full research & financial details"
                >
                  <div>
                    <h3>{item.company_name || symbol}</h3>
                    <p className="history-symbol">
                      Stock Symbol: <strong>{symbol}</strong>
                      {item.analysis_period && ` • Period: ${item.analysis_period}`}
                    </p>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
                    <div className="history-date">
                      <span>Research Date</span>
                      <p>
                        {item.created_at
                          ? new Date(item.created_at).toLocaleString()
                          : "Recently"}
                      </p>
                    </div>

                    <button
                      onClick={(e) => handleDelete(item.id, e)}
                      style={{
                        background: "transparent",
                        color: "#ef4444",
                        border: "1px solid #ef4444",
                        borderRadius: "6px",
                        padding: "6px 10px",
                        fontSize: "12px",
                        cursor: "pointer"
                      }}
                      title="Remove this research entry"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default ResearchHistory;
