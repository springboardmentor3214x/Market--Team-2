import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

import Register from "./pages/Register";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Watchlist from "./pages/Watchlist";
import Preferences from "./pages/Preferences";
import ResearchHistory from "./pages/ResearchHistory";
import StockResearch from "./pages/StockResearch";

import ProtectedRoute from "./components/ProtectedRoute";

function NotFound() {
  return (
    <div style={{ textAlign: "center", marginTop: "100px", color: "#f3f4f6" }}>
      <h1>404 - Page Not Found</h1>
      <p style={{ color: "#9ca3af", margin: "16px 0" }}>The page you are looking for does not exist.</p>
      <Link to="/dashboard" style={{ color: "#38bdf8", textDecoration: "underline" }}>
        Go to Dashboard
      </Link>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Authentication Routes */}
        <Route path="/" element={<Register />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />

        {/* Dashboard */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* Module 1 Routes */}
        <Route
          path="/watchlist"
          element={
            <ProtectedRoute>
              <Watchlist />
            </ProtectedRoute>
          }
        />

        <Route
          path="/preferences"
          element={
            <ProtectedRoute>
              <Preferences />
            </ProtectedRoute>
          }
        />

        <Route
          path="/research-history"
          element={
            <ProtectedRoute>
              <ResearchHistory />
            </ProtectedRoute>
          }
        />

        {/* Module 2 Route */}
        <Route
          path="/stock-research"
          element={
            <ProtectedRoute>
              <StockResearch />
            </ProtectedRoute>
          }
        />

        {/* 404 Route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
