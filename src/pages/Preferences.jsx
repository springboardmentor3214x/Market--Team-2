
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Preferences() {
  const navigate = useNavigate();

  const [market, setMarket] = useState("NSE");
  const [period, setPeriod] = useState("3 months");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        const response = await api.get("/preferences");

        setMarket(response.data.market || "NSE");
        setPeriod(response.data.period || "3 months");
      } catch (error) {
        console.error("Error fetching preferences:", error);
        setError("Unable to load preferences.");
      } finally {
        setLoading(false);
      }
    };

    fetchPreferences();
  }, []);

  const savePreferences = async () => {
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      await api.put("/preferences", {
        market,
        period,
      });

      setSuccess("Preferences saved successfully!");
    } catch (error) {
      console.error("Error saving preferences:", error);
      setError("Unable to save preferences. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="preferences-container">
      <button
        className="back-button"
        onClick={() => navigate("/dashboard")}
      >
        ← Back to Dashboard
      </button>

      <div className="preferences-header">
        <h1>User Preferences</h1>
        <p>Customize your preferred stock market and analysis period.</p>
      </div>

      <div className="preferences-card">
        {loading ? (
          <p>Loading preferences...</p>
        ) : (
          <>
            <div className="preference-field">
              <label>Preferred Market</label>
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value)}
              >
                <option value="NSE">NSE</option>
                <option value="BSE">BSE</option>
                <option value="NYSE">NYSE</option>
                <option value="NASDAQ">NASDAQ</option>
              </select>
            </div>

            <div className="preference-field">
              <label>Analysis Period</label>
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                <option value="1 month">1 month</option>
                <option value="3 months">3 months</option>
                <option value="6 months">6 months</option>
                <option value="1 year">1 year</option>
              </select>
            </div>

            {error && <p className="preferences-error">{error}</p>}
            {success && <p className="preferences-success">{success}</p>}

            <button
              className="save-preferences-button"
              onClick={savePreferences}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save Preferences"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default Preferences;
