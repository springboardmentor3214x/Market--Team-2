import { useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";

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
    <div className="auth-container">
      <h2>Create Account</h2>

      <form onSubmit={handleRegister}>
        <input
          type="email"
          placeholder="Email Address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Password (min 6 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />

        <button type="submit" disabled={loading}>
          {loading ? "Registering..." : "Register"}
        </button>
      </form>

      {message && (
        <p
          className={isSuccess ? "success-message" : "error-message"}
          style={{ color: isSuccess ? "#22c55e" : "#ef4444", marginTop: "10px" }}
        >
          {message}
        </p>
      )}

      {isExistingUser && (
        <p style={{ marginTop: "10px" }}>
          This email is already registered.{" "}
          <Link to="/login" style={{ color: "#38bdf8", fontWeight: "bold" }}>
            Go to Login
          </Link>
        </p>
      )}

      <p style={{ marginTop: "15px" }}>
        Already have an account?{" "}
        <Link to="/login">Login here</Link>
      </p>
    </div>
  );
}

export default Register;
