
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function ResearchHistory() {
  const navigate = useNavigate();

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await api.get("/research-history");
        setHistory(response.data);
      } catch (error) {
        console.error("Error fetching research history:", error);
        setError("Unable to load research history. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  return (
    <div className="history-container">
      <button
        className="back-button"
        onClick={() => navigate("/dashboard")}
      >
        ← Back to Dashboard
      </button>

      <div className="history-header">
        <h1>Research History</h1>
        <p>View your previously researched companies.</p>
      </div>

      <div className="history-content">
        {loading ? (
          <p className="history-message">Loading research history...</p>
        ) : error ? (
          <p className="history-error">{error}</p>
        ) : history.length === 0 ? (
          <div className="history-empty">
            <h3>No Research History Yet</h3>
            <p>Your researched companies will appear here.</p>
            <button onClick={() => navigate("/stock-research")}>
              Start Researching
            </button>
          </div>
        ) : (
          <div className="history-list">
            {history.map((item) => (
              <div className="history-item" key={item.id}>
                <div>
                  <h3>{item.company_name}</h3>
                  <p className="history-symbol">
                    Stock Symbol: {item.stock_symbol}
                  </p>
                </div>

                <div className="history-date">
                  <span>Research Date</span>
                  <p>
                    {item.created_at
                      ? new Date(item.created_at).toLocaleString()
                      : "Date unavailable"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ResearchHistory;
