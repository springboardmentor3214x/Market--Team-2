import { useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";
import { TrendingUp, Lock, Mail, ArrowRight } from "lucide-react";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      setLoading(true);

      const response = await axios.post("http://localhost:8000/login", {
        email,
        password
      });

      const token = response.data.access_token;
      sessionStorage.setItem("token", token);

      navigate("/dashboard");
    } catch (err) {
      const errDetail = err.response?.data?.detail;
      if (Array.isArray(errDetail)) {
        setError(errDetail.map((d) => d.msg).join(", "));
      } else if (typeof errDetail === "string") {
        setError(errDetail);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError("Invalid credentials or server unavailable");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page-wrapper">
      <div className="auth-card">
        <div className="auth-brand-center">
          <div className="brand-icon-wrapper">
            <TrendingUp size={24} />
          </div>
          <h2>Welcome Back</h2>
          <p className="subtitle">Sign in to your Market AI research terminal</p>
        </div>

        {error && <div className="alert-box alert-error" style={{ marginBottom: "20px" }}>{error}</div>}

        <form onSubmit={handleLogin} className="auth-form">
          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              placeholder="user@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: "100%", padding: "12px", marginTop: "8px" }}
          >
            {loading ? "Authenticating..." : "Sign In to Terminal"}
            <ArrowRight size={16} />
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "24px", fontSize: "13.5px", color: "var(--text-secondary)" }}>
          Don't have an account?{" "}
          <Link to="/register" style={{ fontWeight: "700", color: "#60a5fa" }}>
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
