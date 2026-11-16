
import { useState } from "react";
import { useNavigate } from "react-router-dom";

function StockResearch() {
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStock, setSelectedStock] = useState(null);
  const [period, setPeriod] = useState("1 Month");
  const [statement, setStatement] = useState("Income Statement");
  const [error, setError] = useState("");

  const stocks = [
    {
      symbol: "INFY",
      name: "Infosys Limited",
      exchange: "NSE",
      currency: "INR",
      sector: "Information Technology",
      industry: "IT Services",
      price: "1,520.00",
      description: "Infosys is an Indian IT services and consulting company."
    },
    {
      symbol: "TCS",
      name: "Tata Consultancy Services",
      exchange: "BSE",
      currency: "INR",
      sector: "Information Technology",
      industry: "IT Services",
      price: "3,450.00",
      description: "TCS is an Indian IT services and consulting company."
    },
    {
      symbol: "RELIANCE",
      name: "Reliance Industries",
      exchange: "NSE",
      currency: "INR",
      sector: "Energy",
      industry: "Oil and Gas",
      price: "1,280.00",
      description: "Reliance Industries operates in energy, retail and telecommunications."
    },
    {
      symbol: "AAPL",
      name: "Apple Inc.",
      exchange: "NASDAQ",
      currency: "USD",
      sector: "Technology",
      industry: "Consumer Electronics",
      price: "225.00",
      description: "Apple is an American technology company known for consumer electronics and software."
    },
    {
      symbol: "IBM",
      name: "International Business Machines",
      exchange: "NYSE",
      currency: "USD",
      sector: "Technology",
      industry: "IT Services",
      price: "210.00",
      description: "IBM provides IT services, software and cloud solutions."
    }
  ];

  const samplePrices = [
    { date: "2026-11-13", open: "1,500.00", high: "1,535.00", low: "1,490.00", close: "1,520.00", volume: "1,250,000" },
    { date: "2026-11-12", open: "1,480.00", high: "1,510.00", low: "1,470.00", close: "1,500.00", volume: "1,100,000" },
    { date: "2026-11-11", open: "1,460.00", high: "1,495.00", low: "1,450.00", close: "1,480.00", volume: "980,000" },
    { date: "2026-10-15", open: "1,430.00", high: "1,465.00", low: "1,420.00", close: "1,450.00", volume: "900,000" },
    { date: "2026-08-15", open: "1,380.00", high: "1,410.00", low: "1,370.00", close: "1,400.00", volume: "850,000" },
    { date: "2026-05-15", open: "1,300.00", high: "1,340.00", low: "1,290.00", close: "1,320.00", volume: "800,000" }
  ];

  const periodMonths = {
    "1 Month": 1,
    "3 Months": 3,
    "6 Months": 6,
    "1 Year": 12
  };

  const filteredPrices =
    selectedStock?.symbol === "INFY"
      ? samplePrices.filter((item) => {
          const recordDate = new Date(item.date);
          const latestDate = new Date("2026-11-16");
          const startDate = new Date(latestDate);

          startDate.setMonth(
            startDate.getMonth() - periodMonths[period]
          );

          return recordDate >= startDate && recordDate <= latestDate;
        })
      : [];

  const financialStatements = {
    "Income Statement": [
      { label: "Revenue", value: "₹25,000 Cr" },
      { label: "Operating Expenses", value: "₹18,000 Cr" },
      { label: "Net Income", value: "₹5,000 Cr" }
    ],
    "Balance Sheet": [
      { label: "Total Assets", value: "₹80,000 Cr" },
      { label: "Total Liabilities", value: "₹30,000 Cr" },
      { label: "Shareholders' Equity", value: "₹50,000 Cr" }
    ],
    "Cash Flow Statement": [
      { label: "Operating Cash Flow", value: "₹7,000 Cr" },
      { label: "Investing Cash Flow", value: "-₹2,000 Cr" },
      { label: "Financing Cash Flow", value: "-₹1,000 Cr" }
    ]
  };

  const unavailableStatements = ["IBM"];

  // DATA VALIDATION

  const hasMissingValues = samplePrices.some((item) =>
    Object.values(item).some(
      (value) => value === "" || value === null || value === undefined
    )
  );

  const dates = samplePrices.map((item) => item.date);
  const hasDuplicateDates = new Set(dates).size !== dates.length;

  const hasInvalidDates = samplePrices.some((item) => {
    const date = new Date(item.date);

    return (
      Number.isNaN(date.getTime()) ||
      date.toISOString().slice(0, 10) !== item.date
    );
  });

  const hasInvalidNumbers = samplePrices.some((item) =>
    ["open", "high", "low", "close", "volume"].some((key) => {
      const value = Number(String(item[key]).replace(/,/g, ""));
      return !Number.isFinite(value) || value < 0;
    })
  );

  const hasInvalidOHLC = samplePrices.some((item) => {
    const open = Number(item.open.replace(/,/g, ""));
    const high = Number(item.high.replace(/,/g, ""));
    const low = Number(item.low.replace(/,/g, ""));
    const close = Number(item.close.replace(/,/g, ""));

    return (
      high < Math.max(open, low, close) ||
      low > Math.min(open, high, close)
    );
  });

  const validationChecks = [
    { label: "Missing values", passed: !hasMissingValues },
    { label: "Duplicate dates", passed: !hasDuplicateDates },
    { label: "Date formats", passed: !hasInvalidDates },
    { label: "Numeric formats", passed: !hasInvalidNumbers },
    { label: "OHLC consistency", passed: !hasInvalidOHLC }
  ];

  const allValid = validationChecks.every(
    (check) => check.passed
  );

  const handleSearch = (e) => {
    e.preventDefault();
    setError("");
    setSelectedStock(null);

    const term = searchTerm.trim().toLowerCase();

    if (!term) {
      setError("Please enter a company name or stock symbol.");
      return;
    }

    const result = stocks.find(
      (stock) =>
        stock.symbol.toLowerCase() === term ||
        stock.name.toLowerCase().includes(term)
    );

    if (result) {
      setSelectedStock(result);
    } else {
      setError("Company not found. Please enter a valid stock symbol.");
    }
  };

  return (
    <div className="stock-research">

      <button
        type="button"
        onClick={() => navigate("/dashboard")}
      >
        ← Back to Dashboard
      </button>

      <h1>Stock Research</h1>

      <p>Search companies and explore stock market information.</p>

      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Enter company name or ticker (e.g. INFY)"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setError("");
            setSelectedStock(null);
          }}
        />

        <button type="submit">Search</button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {selectedStock && (
        <>
          <div className="stock-details">
            <h2>{selectedStock.name}</h2>
            <h3>{selectedStock.symbol}</h3>

            <p><strong>Description:</strong> {selectedStock.description}</p>
            <p><strong>Exchange:</strong> {selectedStock.exchange}</p>
            <p><strong>Currency:</strong> {selectedStock.currency}</p>
            <p><strong>Sector:</strong> {selectedStock.sector}</p>
            <p><strong>Industry:</strong> {selectedStock.industry}</p>

            <h2>{selectedStock.currency} {selectedStock.price}</h2>
            <p>Illustrative sample price - not live market data.</p>
          </div>

          <div className="historical-prices">
            <h2>Historical Stock Prices</h2>

            {selectedStock.symbol !== "INFY" && (
              <p>
                Historical sample data is currently available only for
                Infosys. Data for other companies will be displayed
                after API integration.
              </p>
            )}

            <label>Select Period: </label>

            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              <option value="1 Month">1 Month</option>
              <option value="3 Months">3 Months</option>
              <option value="6 Months">6 Months</option>
              <option value="1 Year">1 Year</option>
            </select>

            <p>Selected period: {period}</p>
            <h3>OHLCV Data</h3>

            {filteredPrices.length > 0 && (
              <table border="1" cellPadding="10">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                    <th>Volume</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredPrices.map((item) => (
                    <tr key={item.date}>
                      <td>{item.date}</td>
                      <td>{item.open}</td>
                      <td>{item.high}</td>
                      <td>{item.low}</td>
                      <td>{item.close}</td>
                      <td>{item.volume}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {selectedStock.symbol === "INFY" &&
              filteredPrices.length === 0 && (
                <p>No historical records available for this period.</p>
              )}

            <p>Illustrative sample data, not actual market prices.</p>
          </div>

          <div className="financial-statements">
            <h2>Financial Statements</h2>

            <label>Select Statement: </label>

            <select
              value={statement}
              onChange={(e) => setStatement(e.target.value)}
            >
              <option value="Income Statement">Income Statement</option>
              <option value="Balance Sheet">Balance Sheet</option>
              <option value="Cash Flow Statement">Cash Flow Statement</option>
            </select>

            <h3>{statement}</h3>

            {unavailableStatements.includes(selectedStock.symbol) ? (
              <p>
                Financial statement data is currently unavailable for{" "}
                {selectedStock.name}.
              </p>
            ) : (
              <>
                <table border="1" cellPadding="10">
                  <thead>
                    <tr>
                      <th>Financial Metric</th>
                      <th>Value</th>
                    </tr>
                  </thead>

                  <tbody>
                    {financialStatements[statement].map((item) => (
                      <tr key={item.label}>
                        <td>{item.label}</td>
                        <td>{item.value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <p>
                  Illustrative sample values only. Actual financial data
                  is not connected yet.
                </p>
              </>
            )}
          </div>

          <div className="data-metadata">
            <h2>Data Source & Validation</h2>

            <p><strong>Data Provider:</strong> Alpha Vantage (planned)</p>
            <p><strong>Retrieved At:</strong> Sample timestamp (demo)</p>

            <p>
              <strong>Latest Trading Date:</strong>{" "}
              {filteredPrices.length > 0
                ? filteredPrices[0].date
                : "No trading records available"}
            </p>

            <p>
              <strong>Data Status:</strong>{" "}
              {allValid
                ? "All sample validation checks passed"
                : "Some validation checks failed"}
            </p>

            <h3>Data Validation Results</h3>

            <ul>
              {validationChecks.map((check) => (
                <li key={check.label}>
                  {check.label}:{" "}
                  <strong style={{ color: check.passed ? "green" : "red" }}>
                    {check.passed ? "Passed" : "Failed"}
                  </strong>
                </li>
              ))}
            </ul>

            <p>
              Validation is currently performed on illustrative sample
              data in the frontend.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

export default StockResearch;
