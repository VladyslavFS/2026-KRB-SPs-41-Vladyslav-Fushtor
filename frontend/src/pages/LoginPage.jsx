import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login, register, user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) {
    return (
      <div className="main">
        <div className="page-header">
          <h2>Account</h2>
        </div>
        <div className="info-box info-box--success">
          Signed in as {user.email}
        </div>
      </div>
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);

    const action = tab === "login" ? login : register;
    const result = await action(email, password);

    setBusy(false);
    if (result.ok) {
      navigate("/");
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="main">
      <div className="page-header">
        <h2>Authentication</h2>
        <p className="page-header__sub">Sign in to save events and manage alert rules</p>
      </div>

      <div className="card" style={{ maxWidth: 420 }}>
        <div className="tabs">
          <button
            className={`tab${tab === "login" ? " tab--active" : ""}`}
            onClick={() => { setTab("login"); setError(""); }}
          >
            Sign In
          </button>
          <button
            className={`tab${tab === "register" ? " tab--active" : ""}`}
            onClick={() => { setTab("register"); setError(""); }}
          >
            Register
          </button>
        </div>

        {error && <div className="info-box info-box--error mb-12">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              className="form-input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              className="form-input"
              type="password"
              placeholder="Min 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          <button
            type="submit"
            className="btn btn--primary btn--full"
            disabled={busy}
          >
            {busy ? "Loading..." : tab === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
