import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiForgotPassword } from "../api/client";

export default function LoginPage() {
  const { login, register, user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("login"); // login | register | forgot
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [devToken, setDevToken] = useState("");
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
    setSuccess("");
    setDevToken("");
    setBusy(true);

    if (tab === "forgot") {
      const result = await apiForgotPassword(email);
      setBusy(false);
      if (result?.ok) {
        setSuccess("Password reset instructions have been sent to your email.");
        if (result.data?.reset_token_dev) {
          setDevToken(result.data.reset_token_dev);
        }
      } else {
        setError(result?.error || "Failed to send reset link.");
      }
      return;
    }

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
    <div className="main" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "80vh" }}>
      <div className="page-header" style={{ textAlign: "center", marginBottom: 24 }}>
        <h2>Authentication</h2>
        <p className="page-header__sub">Sign in to save events and manage alert rules</p>
      </div>

      <div className="card" style={{ width: "100%", maxWidth: 420 }}>
        {tab !== "forgot" ? (
          <div className="tabs">
            <button
              className={`tab${tab === "login" ? " tab--active" : ""}`}
              onClick={() => { setTab("login"); setError(""); setSuccess(""); }}
            >
              Sign In
            </button>
            <button
              className={`tab${tab === "register" ? " tab--active" : ""}`}
              onClick={() => { setTab("register"); setError(""); setSuccess(""); }}
            >
              Register
            </button>
          </div>
        ) : (
          <div className="tabs">
            <button className="tab tab--active">
              Reset Password
            </button>
          </div>
        )}

        {error && <div className="info-box info-box--error mb-12">{error}</div>}
        {success && <div className="info-box info-box--success mb-12">{success}</div>}

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

          {tab !== "forgot" && (
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
              {tab === "login" && (
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 6 }}>
                  <a
                    href="#forgot"
                    style={{ fontSize: 12, color: "var(--accent)", textDecoration: "none" }}
                    onClick={(e) => {
                      e.preventDefault();
                      setTab("forgot");
                      setError("");
                      setSuccess("");
                    }}
                  >
                    Forgot password?
                  </a>
                </div>
              )}
            </div>
          )}

          <button
            type="submit"
            className="btn btn--primary btn--full"
            disabled={busy}
          >
            {busy
              ? "Loading..."
              : tab === "login"
              ? "Sign In"
              : tab === "register"
              ? "Create Account"
              : "Send Reset Link"}
          </button>

          {tab === "forgot" && (
            <div style={{ textAlign: "center", marginTop: 16 }}>
              <a
                href="#login"
                style={{ fontSize: 13, color: "var(--text-secondary)", textDecoration: "none" }}
                onClick={(e) => {
                  e.preventDefault();
                  setTab("login");
                  setError("");
                  setSuccess("");
                  setDevToken("");
                }}
              >
                Back to Sign In
              </a>
            </div>
          )}

          {devToken && (
            <a
              href={`/reset-password?token=${devToken}`}
              className="btn btn--ghost btn--full mt-12"
              style={{ borderColor: "var(--success)", color: "var(--success)" }}
            >
              [Dev Mode] Reset Password Now
            </a>
          )}
        </form>
      </div>
    </div>
  );
}
