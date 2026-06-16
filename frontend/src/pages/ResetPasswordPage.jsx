import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiResetPassword } from "../api/client";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!token) {
      setError("Reset token is missing from the URL.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);
    const result = await apiResetPassword(token, password);
    setBusy(false);

    if (result?.ok) {
      setSuccess("Your password has been successfully reset.");
      setPassword("");
      setConfirmPassword("");
    } else {
      setError(result?.data?.error?.message || "Failed to reset password. The token may be invalid or expired.");
    }
  }

  return (
    <div className="main" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "80vh" }}>
      <div className="page-header" style={{ textAlign: "center", marginBottom: 24 }}>
        <h2>Reset Password</h2>
        <p className="page-header__sub">Create a new secure password for your account</p>
      </div>

      <div className="card" style={{ width: "100%", maxWidth: 420 }}>
        {error && <div className="info-box info-box--error mb-12">{error}</div>}
        {success && (
          <div className="info-box info-box--success mb-12">
            <div>
              <p>{success}</p>
              <button
                className="btn btn--primary btn--sm mt-12"
                onClick={() => navigate("/login")}
              >
                Go to Sign In
              </button>
            </div>
          </div>
        )}

        {!success && (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="password">New Password</label>
              <input
                id="password"
                className="form-input"
                type="password"
                placeholder="Min 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                id="confirmPassword"
                className="form-input"
                type="password"
                placeholder="Repeat new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <button
              type="submit"
              className="btn btn--primary btn--full"
              disabled={busy || !token}
            >
              {busy ? "Resetting..." : "Reset Password"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
