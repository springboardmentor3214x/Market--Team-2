import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Search,
  Bookmark,
  Clock,
  Settings,
  LogOut,
  Sparkles,
  TrendingUp
} from "lucide-react";

function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    sessionStorage.removeItem("token");
    navigate("/login");
  };

  const navLinks = [
    { path: "/dashboard", label: "Dashboard", icon: BarChart3 },
    { path: "/stock-research", label: "Stock Research", icon: Search },
    { path: "/watchlist", label: "Watchlist", icon: Bookmark },
    { path: "/research-history", label: "History", icon: Clock },
    { path: "/preferences", label: "Preferences", icon: Settings },
  ];

  return (
    <header className="app-navbar">
      <div className="navbar-container">
        {/* Brand */}
        <Link to="/dashboard" className="navbar-brand">
          <div className="brand-icon-wrapper">
            <TrendingUp size={20} className="brand-icon" />
          </div>
          <div className="brand-text-group">
            <span className="brand-name">Market AI</span>
            <span className="brand-badge">Multi-Agent</span>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="navbar-nav">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`nav-link ${isActive ? "active" : ""}`}
              >
                <Icon size={16} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Actions */}
        <div className="navbar-actions">
          <div className="market-status-pill">
            <span className="pulse-dot"></span>
            <span>Markets Live</span>
          </div>

          <button onClick={handleLogout} className="logout-btn" title="Sign Out">
            <LogOut size={16} />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
