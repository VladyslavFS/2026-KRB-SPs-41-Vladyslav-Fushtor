import { createContext, useContext, useEffect, useState } from "react";
import { apiGetMe, apiLogin, apiLogout, apiRegister } from "../api/client";

const AuthContext = createContext(null);

const TOKEN_KEY = "eq_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!localStorage.getItem(TOKEN_KEY));

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    apiGetMe(token).then((res) => {
      if (res?.ok) {
        setUser(res.data);
      } else {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      }
      setLoading(false);
    });
  }, [token]);

  function saveToken(t) {
    if (t) {
      localStorage.setItem(TOKEN_KEY, t);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
    setToken(t);
  }

  async function login(email, password) {
    const res = await apiLogin(email, password);
    if (res?.ok) {
      saveToken(res.data.token.access_token);
      setUser(res.data.user);
      return { ok: true };
    }
    return { ok: false, error: "Invalid email or password" };
  }

  async function register(email, password) {
    const res = await apiRegister(email, password);
    if (res?.ok) {
      saveToken(res.data.token.access_token);
      setUser(res.data.user);
      return { ok: true };
    }
    return { ok: false, error: "Registration failed. Email may already exist." };
  }

  async function logout() {
    await apiLogout(token);
    saveToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ token, user, loading, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
