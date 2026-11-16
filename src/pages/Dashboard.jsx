
import { Link, useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();

  const handleLogout = () => {
    sessionStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Welcome to Market Research AI</h1>
          <p>Your personal stock research workspace</p>
        </div>

        <button onClick={handleLogout}>Logout</button>
      </div>

      <div className="dashboard-cards">
        <Link to="/stock-research" className="dashboard-card">
          <h3>Stock Research</h3>
          <p>Search stocks and explore historical prices, company profiles and financial statements.</p>
        </Link>

        <Link to="/research-history" className="dashboard-card">
          <h3>Research History</h3>
          <p>View your previous research activities.</p>
        </Link>

        <Link to="/watchlist" className="dashboard-card">
          <h3>My Watchlist</h3>
          <p>Keep track of your selected stocks.</p>
        </Link>

        <Link to="/preferences" className="dashboard-card">
          <h3>Preferences</h3>
          <p>Manage your research preferences.</p>
        </Link>

        <Link to="/profile" className="dashboard-card">
          <h3>My Profile</h3>
          <p>View and manage your account details.</p>
        </Link>
      </div>
    </div>
  );
}

export default Dashboard;
