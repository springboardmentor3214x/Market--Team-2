import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

import Register from "./pages/Register";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Watchlist from "./pages/Watchlist";
import Preferences from "./pages/Preferences";
import ResearchHistory from "./pages/ResearchHistory";
import StockResearch from "./pages/StockResearch";

import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

function NotFound() {
  return (
    <div className="not-found-container">
      <div className="not-found-card">
        <h1>404</h1>
        <h2>Page Not Found</h2>
        <p>The stock research page or route you are looking for does not exist.</p>
        <Link to="/dashboard" className="btn-primary">
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Authentication Routes */}
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected Application Routes wrapped in Layout (Navbar + Content Container) */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/stock-research" element={<StockResearch />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/research-history" element={<ResearchHistory />} />
          <Route path="/preferences" element={<Preferences />} />
        </Route>

        {/* 404 Route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
