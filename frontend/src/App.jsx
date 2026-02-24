import { BrowserRouter, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";

// Placeholder pages — will be replaced in R3/R4
function FeedPage() {
  return (
    <div className="main">
      <div className="page-header">
        <h2>Earthquake Feed</h2>
        <p className="page-header__sub">Real-time seismic activity monitoring</p>
      </div>
      <div className="info-box info-box--info">
        Feed page coming in R3.
      </div>
    </div>
  );
}

function TopEventsPage() {
  return (
    <div className="main">
      <div className="page-header">
        <h2>Top Events Daily</h2>
        <p className="page-header__sub">Strongest earthquakes by day</p>
      </div>
      <div className="info-box info-box--info">
        Top Events page coming in R4.
      </div>
    </div>
  );
}

function SavedEventsPage() {
  return (
    <div className="main">
      <div className="page-header">
        <h2>Saved Events</h2>
        <p className="page-header__sub">Your bookmarked earthquakes</p>
      </div>
      <div className="info-box info-box--info">
        Saved Events page coming in R4.
      </div>
    </div>
  );
}

function AlertRulesPage() {
  return (
    <div className="main">
      <div className="page-header">
        <h2>Alert Rules</h2>
        <p className="page-header__sub">Manage notification criteria</p>
      </div>
      <div className="info-box info-box--info">
        Alert Rules page coming in R4.
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="app">
          <Sidebar />
          <Routes>
            <Route path="/" element={<FeedPage />} />
            <Route path="/top-events" element={<TopEventsPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/saved"
              element={
                <ProtectedRoute>
                  <SavedEventsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/alerts"
              element={
                <ProtectedRoute>
                  <AlertRulesPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
