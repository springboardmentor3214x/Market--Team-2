import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Clock,
  Trash2,
  ArrowRight,
  RotateCcw,
  Search,
  AlertCircle
} from "lucide-react";
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
      setMessage("All research history cleared successfully.");
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
    <div className="history-page">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "26px", fontWeight: "800", color: "#ffffff", letterSpacing: "-0.4px" }}>
            Research History
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "4px" }}>
            Audit log of previously researched stocks, telemetry parameters, and timestamps.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          {history.length > 0 && (
            <button
              type="button"
              onClick={handleClearAll}
              className="btn-danger"
            >
              <Trash2 size={14} />
              <span>Clear History</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="back-button"
          >
            &larr; Back to Dashboard
          </button>
        </div>
      </div>

      {message && <div className="alert-box alert-success" style={{ marginBottom: "20px" }}>{message}</div>}
      {error && <div className="alert-box alert-error" style={{ marginBottom: "20px" }}>{error}</div>}

      {/* History Table / Panel */}
      <div className="tab-content-panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ fontSize: "16px", fontWeight: "700", color: "#ffffff", display: "flex", alignItems: "center", gap: "8px" }}>
            <Clock size={18} style={{ color: "var(--warning-amber)" }} />
            Logged Inquiries ({history.length})
          </h3>
        </div>

        {loading ? (
          <p style={{ color: "var(--text-muted)", padding: "20px 0" }}>Loading research audit logs...</p>
        ) : history.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px 20px", color: "var(--text-secondary)" }}>
            <Clock size={36} style={{ color: "var(--text-muted)", marginBottom: "12px" }} />
            <h4 style={{ color: "#ffffff", fontSize: "16px", marginBottom: "6px" }}>No Research Records Found</h4>
            <p style={{ fontSize: "13.5px", maxWidth: "380px", margin: "0 auto" }}>
              Stocks you search in Stock Research will automatically be logged here for easy reference.
            </p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="fin-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Company Name</th>
                  <th>Window</th>
                  <th>Queried At</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => {
                  const symbol = item.stock_symbol || item.ticker_symbol;
                  return (
                    <tr key={item.id}>
                      <td>
                        <span style={{ fontWeight: "800", color: "#60a5fa", fontFamily: "var(--font-mono)", fontSize: "15px" }}>
                          {symbol}
                        </span>
                      </td>
                      <td>{item.company_name || symbol}</td>
                      <td>
                        <span className="exchange-pill">
                          {item.analysis_period || "3mo"}
                        </span>
                      </td>
                      <td style={{ color: "var(--text-muted)", fontSize: "12px" }}>
                        {item.created_at ? new Date(item.created_at).toLocaleString() : "Recent"}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "8px" }}>
                          <button
                            type="button"
                            onClick={() => handleOpenStock(symbol)}
                            className="btn-secondary"
                            style={{ padding: "6px 12px", fontSize: "12px" }}
                          >
                            <span>Re-analyze</span>
                            <ArrowRight size={13} />
                          </button>
                          <button
                            type="button"
                            onClick={(e) => handleDelete(item.id, e)}
                            className="btn-danger"
                            style={{ padding: "6px 10px" }}
                            title="Delete entry"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default ResearchHistory;
