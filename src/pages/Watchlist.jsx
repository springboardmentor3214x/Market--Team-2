import { useEffect, useState } from "react";
import api from "../services/api";

function Watchlist() {

  const [stocks, setStocks] = useState([]);
  const [symbol, setSymbol] = useState("");

  const fetchStocks = async () => {
    const response = await api.get("/watchlist");
    setStocks(response.data);
  };

  useEffect(() => {
    fetchStocks();
  }, []);

  const addStock = async () => {

    if (!symbol.trim()) return;

    await api.post("/watchlist", {
      symbol: symbol.toUpperCase()
    });

    setSymbol("");
    fetchStocks();
  };

  const removeStock = async (id) => {

    await api.delete(`/watchlist/${id}`);

    fetchStocks();
  };

  return (
    <div>
      <h2>My Watchlist</h2>

      <input
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
        placeholder="Enter stock symbol"
      />

      <button onClick={addStock}>Add Stock</button>

      {stocks.map((stock) => (
        <div key={stock.id}>
          {stock.symbol}

          <button onClick={() => removeStock(stock.id)}>
            Remove
          </button>
        </div>
      ))}
    </div>
  );
}

export default Watchlist;