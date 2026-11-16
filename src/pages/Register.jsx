import { useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setMessage("");

    if (password !== confirmPassword) {
      setMessage("Passwords do not match");
      setIsSuccess(false);
      return;
    }

    try {
      const response = await axios.post(
        "http://localhost:8000/register",
        {
          email,
          password
        }
      );

      setMessage("Registration successful! You can now log in.");
      setIsSuccess(true);
      setEmail("");
      setPassword("");
      setConfirmPassword("");

    } catch (error) {
      setIsSuccess(false);
      const errDetail = error.response?.data?.detail;
      if (Array.isArray(errDetail)) {
        setMessage(errDetail.map((d) => d.msg).join(", "));
      } else if (typeof errDetail === "string") {
        setMessage(errDetail);
      } else if (error.message) {
        setMessage(error.message);
      } else {
        setMessage("Registration failed. Please ensure the backend is running.");
      }
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

        <button type="submit">Register</button>
      </form>

      {message && (
        <p style={{ color: isSuccess ? "green" : "red", marginTop: "10px" }}>
          {message}
        </p>
      )}

      <p style={{ marginTop: "15px" }}>
        Already have an account? <Link to="/login">Login here</Link>
      </p>
    </div>
  );
}

export default Register;
