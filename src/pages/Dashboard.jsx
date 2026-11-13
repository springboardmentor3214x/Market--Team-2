import { Link } from "react-router-dom";

function Dashboard() {

  return (
    <div className="dashboard">

      <h1>Welcome to Market Research AI</h1>

      <p>Your personal research workspace</p>

      <div className="dashboard-cards">

        <Link to="/research-history">
          Research History
        </Link>

        <Link to="/watchlist">
          My Watchlist
        </Link>

        <Link to="/preferences">
          Preferences
        </Link>

        <Link to="/profile">
          My Profile
        </Link>

      </div>

    </div>
  );
}

export default Dashboard;