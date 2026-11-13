import { useEffect, useState } from "react";
import api from "../services/api";

function Preferences() {

  const [market, setMarket] = useState("NSE");
  const [period, setPeriod] = useState("3 months");

  useEffect(() => {

    api.get("/preferences")
      .then(response => {
        setMarket(response.data.market);
        setPeriod(response.data.period);
      })
      .catch(console.error);

  }, []);

  const savePreferences = async () => {

    await api.put("/preferences", {
      market,
      period
    });

    alert("Preferences saved!");
  };

  return (
    <div>
      <h2>User Preferences</h2>

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

      <label>Analysis Period</label>

      <select
        value={period}
        onChange={(e) => setPeriod(e.target.value)}
      >
        <option>1 month</option>
        <option>3 months</option>
        <option>6 months</option>
        <option>1 year</option>
      </select>

      <button onClick={savePreferences}>
        Save Preferences
      </button>

    </div>
  );
}

export default Preferences;