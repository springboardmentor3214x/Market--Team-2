import { useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";

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

      const response = await axios.post(
        "http://localhost:8000/login",
        {
          email,
          password
        }
      );

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
    <div className="auth-container">
      <h2>Login</h2>

      <form onSubmit={handleLogin}>
        <input
          type="email"
          placeholder="Email Address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>

      {error && (
        <p className="error-message" style={{ color: "#ef4444", marginTop: "10px" }}>
          {error}
        </p>
      )}

      <p style={{ marginTop: "15px" }}>
        Don't have an account?{" "}
        <Link to="/register">Register here</Link>
      </p>
    </div>
  );
}

export default Login;
