import { BrowserRouter, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import FeedPage from "./pages/FeedPage";
import TopEventsPage from "./pages/TopEventsPage";
import SavedEventsPage from "./pages/SavedEventsPage";
import AlertRulesPage from "./pages/AlertRulesPage";
import LoginPage from "./pages/LoginPage";

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
