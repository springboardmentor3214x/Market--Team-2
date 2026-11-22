import { useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";
import { TrendingUp, ArrowRight, CheckCircle2 } from "lucide-react";

function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [isExistingUser, setIsExistingUser] = useState(false);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setMessage("");
    setIsExistingUser(false);
    setIsSuccess(false);

    if (password !== confirmPassword) {
      setMessage("Passwords do not match");
      return;
    }

    try {
      setLoading(true);

      await axios.post("http://localhost:8000/register", {
        email,
        password
      });

      setMessage("Registration successful! Redirecting to login...");
      setIsSuccess(true);
      setEmail("");
      setPassword("");
      setConfirmPassword("");

      setTimeout(() => {
        navigate("/login");
      }, 1200);

    } catch (error) {
      setIsSuccess(false);
      const errDetail = error.response?.data?.detail;
      let errMsg = "Registration failed. Please ensure the backend is running.";

      if (Array.isArray(errDetail)) {
        errMsg = errDetail.map((d) => d.msg).join(", ");
      } else if (typeof errDetail === "string") {
        errMsg = errDetail;
      } else if (error.message) {
        errMsg = error.message;
      }

      setMessage(errMsg);

      if (
        typeof errMsg === "string" &&
        (errMsg.toLowerCase().includes("already exists") ||
         errMsg.toLowerCase().includes("already registered"))
      ) {
        setIsExistingUser(true);
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
          <h2>Create Account</h2>
          <p className="subtitle">Join Market AI for multi-agent financial research</p>
        </div>

        {message && (
          <div className={`alert-box ${isSuccess ? "alert-success" : "alert-error"}`} style={{ marginBottom: "20px" }}>
            {message}
          </div>
        )}

        <form onSubmit={handleRegister} className="auth-form">
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
              placeholder="Min 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              placeholder="Re-enter password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: "100%", padding: "12px", marginTop: "8px" }}
          >
            {loading ? "Creating Account..." : "Create Account"}
            <ArrowRight size={16} />
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "24px", fontSize: "13.5px", color: "var(--text-secondary)" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ fontWeight: "700", color: "#60a5fa" }}>
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
