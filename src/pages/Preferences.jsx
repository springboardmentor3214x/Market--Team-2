import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Settings,
  Save,
  Globe,
  Calendar,
  CheckCircle2,
  Sparkles
} from "lucide-react";
import api from "../services/api";

function Preferences() {
  const navigate = useNavigate();

  const [market, setMarket] = useState("NSE");
  const [period, setPeriod] = useState("3 months");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const marketOptions = [
    { id: "NSE", name: "National Stock Exchange", region: "India (INR)", flag: "🇮🇳", desc: "Equities, Nifty 50, FnO" },
    { id: "BSE", name: "Bombay Stock Exchange", region: "India (INR)", flag: "🇮🇳", desc: "Equities, Sensex 30" },
    { id: "NASDAQ", name: "NASDAQ Global Market", region: "United States (USD)", flag: "🇺🇸", desc: "Tech Giants, Apple, Microsoft, Nvidia" },
    { id: "NYSE", name: "New York Stock Exchange", region: "United States (USD)", flag: "🇺🇸", desc: "Traditional Blue Chips, Financials" }
  ];

  const periodOptions = [
    { id: "1 month", label: "1 Month", desc: "Short-term momentum" },
    { id: "3 months", label: "3 Months", desc: "Quarterly earnings trend (Default)" },
    { id: "6 months", label: "6 Months", desc: "Mid-term cyclical swing" },
    { id: "1 year", label: "1 Year", desc: "Annual performance & fundamentals" }
  ];

  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        const response = await api.get("/preferences");
        setMarket(response.data.market || "NSE");
        setPeriod(response.data.period || "3 months");
      } catch (err) {
        console.error("Error fetching preferences:", err);
        setError("Unable to load preferences.");
      } finally {
        setLoading(false);
      }
    };

    fetchPreferences();
  }, []);

  const savePreferences = async (e) => {
    if (e) e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      await api.put("/preferences", {
        market,
        period,
      });

      setSuccess("Preferences updated successfully!");
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      console.error("Error saving preferences:", err);
      setError("Unable to save preferences. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="preferences-page">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "26px", fontWeight: "800", color: "#ffffff", letterSpacing: "-0.4px" }}>
            User Preferences
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "4px" }}>
            Customize default market exchanges and analysis duration for the multi-agent system.
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

      {success && <div className="alert-box alert-success" style={{ marginBottom: "20px" }}>{success}</div>}
      {error && <div className="alert-box alert-error" style={{ marginBottom: "20px" }}>{error}</div>}

      <div className="tab-content-panel">
        {loading ? (
          <p style={{ color: "var(--text-muted)", padding: "20px 0" }}>Loading preferences...</p>
        ) : (
          <form onSubmit={savePreferences} style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
            {/* Preferred Market Card Selection */}
            <div>
              <label style={{ fontSize: "14px", fontWeight: "700", color: "#ffffff", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                <Globe size={18} style={{ color: "var(--neutral-blue)" }} />
                Default Market Exchange
              </label>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "14px" }}>
                {marketOptions.map((opt) => {
                  const isSelected = market === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setMarket(opt.id)}
                      style={{
                        padding: "16px 18px",
                        background: isSelected ? "rgba(37, 99, 235, 0.12)" : "var(--bg-secondary)",
                        border: `1px solid ${isSelected ? "var(--accent-primary)" : "var(--border-subtle)"}`,
                        borderRadius: "var(--radius-md)",
                        cursor: "pointer",
                        transition: "all var(--transition-fast)",
                        display: "flex",
                        flexDirection: "column",
                        gap: "6px"
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "15px", fontWeight: "800", color: isSelected ? "#60a5fa" : "#ffffff", fontFamily: "var(--font-mono)" }}>
                          {opt.flag} {opt.id}
                        </span>
                        {isSelected && <CheckCircle2 size={16} style={{ color: "var(--accent-primary)" }} />}
                      </div>
                      <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-primary)" }}>
                        {opt.name}
                      </span>
                      <span style={{ fontSize: "11.5px", color: "var(--text-muted)" }}>
                        {opt.desc}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Default Analysis Window */}
            <div>
              <label style={{ fontSize: "14px", fontWeight: "700", color: "#ffffff", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                <Calendar size={18} style={{ color: "var(--warning-amber)" }} />
                Default Analysis Period
              </label>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px" }}>
                {periodOptions.map((p) => {
                  const isSelected = period.toLowerCase() === p.id.toLowerCase();
                  return (
                    <div
                      key={p.id}
                      onClick={() => setPeriod(p.id)}
                      style={{
                        padding: "14px 16px",
                        background: isSelected ? "rgba(37, 99, 235, 0.12)" : "var(--bg-secondary)",
                        border: `1px solid ${isSelected ? "var(--accent-primary)" : "var(--border-subtle)"}`,
                        borderRadius: "var(--radius-md)",
                        cursor: "pointer",
                        transition: "all var(--transition-fast)"
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "14px", fontWeight: "700", color: isSelected ? "#60a5fa" : "#ffffff" }}>
                          {p.label}
                        </span>
                        {isSelected && <CheckCircle2 size={15} style={{ color: "var(--accent-primary)" }} />}
                      </div>
                      <span style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
                        {p.desc}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Save Button */}
            <div style={{ paddingTop: "10px", borderTop: "1px solid var(--border-subtle)" }}>
              <button
                type="submit"
                className="btn-primary"
                disabled={saving}
                style={{ padding: "12px 28px" }}
              >
                <Save size={16} />
                <span>{saving ? "Saving Changes..." : "Save Preferences"}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default Preferences;
