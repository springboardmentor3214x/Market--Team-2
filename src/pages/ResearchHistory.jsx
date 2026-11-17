import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

function ResearchHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get("/research-history");
      setHistory(res.data || []);
    } catch (err) {
      console.error("Error fetching research history:", err);
      setMessage("Failed to load research history.");
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
    } catch (err) {
      console.error("Clear all error:", err);
      alert("Could not clear history");
    }
  };

  const handleOpenStock = (ticker) => {
    navigate(`/dashboard?ticker=${encodeURIComponent(ticker)}`);
  };

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "24px 16px", fontFamily: "sans-serif", textAlign: "left" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #374151", paddingBottom: "16px", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "28px", margin: 0, color: "#f3f4f6" }}>Research History</h1>
          <p style={{ margin: "4px 0 0", color: "#9ca3af", fontSize: "14px" }}>
            Track and revisit your past stock analysis activities (Isolated per user account)
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          {history.length > 0 && (
            <button
              onClick={handleClearAll}
              style={{ background: "#7f1d1d", color: "#fca5a5", border: "none", padding: "8px 14px", borderRadius: "6px", cursor: "pointer", fontSize: "13px" }}
            >
              Clear All
            </button>
          )}
          <Link
            to="/dashboard"
            style={{ background: "#2563eb", color: "#fff", textDecoration: "none", padding: "8px 16px", borderRadius: "6px", fontSize: "13px", fontWeight: 600 }}
          >
            &larr; Back to Dashboard
          </Link>
        </div>
      </div>

      {message && (
        <div style={{ marginBottom: "16px", padding: "10px 14px", background: "#1e293b", border: "1px solid #3b82f6", borderRadius: "6px", color: "#93c5fd", fontSize: "13px" }}>
          {message}
        </div>
      )}

      {loading ? (
        <p style={{ color: "#9ca3af" }}>Loading research history...</p>
      ) : history.length === 0 ? (
        <div style={{ background: "#111827", border: "1px dashed #374151", borderRadius: "10px", padding: "40px", textAlign: "center" }}>
          <p style={{ color: "#9ca3af", fontSize: "16px", marginBottom: "12px" }}>No research activities logged yet.</p>
          <Link
            to="/dashboard?ticker=INFY"
            style={{ color: "#38bdf8", textDecoration: "underline", fontSize: "14px" }}
          >
            Start researching stocks (e.g. INFY, TCS, RELIANCE) on your dashboard &rarr;
          </Link>
        </div>
      ) : (
        <div style={{ display: "grid", gap: "12px" }}>
          {history.map((item) => (
            <div
              key={item.id}
              onClick={() => handleOpenStock(item.stock_symbol || item.ticker_symbol)}
              style={{
                background: "#111827",
                border: "1px solid #374151",
                borderRadius: "8px",
                padding: "16px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                cursor: "pointer",
                transition: "border-color 0.2s"
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#38bdf8")}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#374151")}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "18px", fontWeight: "bold", color: "#60a5fa" }}>
                    {item.stock_symbol || item.ticker_symbol}
                  </span>
                  <span style={{ fontSize: "14px", color: "#f3f4f6" }}>
                    {item.company_name}
                  </span>
                  <span style={{ background: "#374151", color: "#9ca3af", fontSize: "11px", padding: "2px 6px", borderRadius: "4px" }}>
                    Period: {item.analysis_period || "3mo"}
                  </span>
                </div>
                <div style={{ display: "flex", gap: "16px", marginTop: "6px", fontSize: "12px", color: "#6b7280" }}>
                  <span>Searched on: {item.created_at || "Recent"}</span>
                  {item.research_summary?.price && (
                    <span style={{ color: "#10b981" }}>
                      Price: ₹/ ${item.research_summary.price}
                    </span>
                  )}
                  {item.research_summary?.source && (
                    <span>Source: {item.research_summary.source}</span>
                  )}
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span style={{ color: "#38bdf8", fontSize: "13px" }}>Open in Dashboard &rarr;</span>
                <button
                  onClick={(e) => handleDelete(item.id, e)}
                  style={{
                    background: "transparent",
                    color: "#ef4444",
                    border: "1px solid #ef4444",
                    borderRadius: "4px",
                    padding: "4px 8px",
                    fontSize: "12px",
                    cursor: "pointer"
                  }}
                  title="Remove this research entry"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ResearchHistory;
