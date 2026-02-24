import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar__logo">
        <div className="sidebar__logo-mark">EQ</div>
        <span className="sidebar__title">Earthquake Platform</span>
      </div>

      <nav className="sidebar__nav">
        <span className="sidebar__section">Monitoring</span>
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `sidebar__link${isActive ? " sidebar__link--active" : ""}`
          }
        >
          <span className="sidebar__link-dot"></span>
          Feed
        </NavLink>
        <NavLink
          to="/top-events"
          className={({ isActive }) =>
            `sidebar__link${isActive ? " sidebar__link--active" : ""}`
          }
        >
          <span className="sidebar__link-dot"></span>
          Top Events
        </NavLink>

        {user && (
          <>
            <span className="sidebar__section">Personal</span>
            <NavLink
              to="/saved"
              className={({ isActive }) =>
                `sidebar__link${isActive ? " sidebar__link--active" : ""}`
              }
            >
              <span className="sidebar__link-dot"></span>
              Saved Events
            </NavLink>
            <NavLink
              to="/alerts"
              className={({ isActive }) =>
                `sidebar__link${isActive ? " sidebar__link--active" : ""}`
              }
            >
              <span className="sidebar__link-dot"></span>
              Alert Rules
            </NavLink>
          </>
        )}
      </nav>

      <div className="sidebar__spacer"></div>
      <div className="sidebar__divider"></div>

      {user ? (
        <>
          <div className="sidebar__user">
            <div className="sidebar__user-avatar">
              {user.email[0].toUpperCase()}
            </div>
            <span className="sidebar__user-email">{user.email}</span>
          </div>
          <button
            className="btn btn--ghost btn--sm btn--full"
            onClick={logout}
            style={{ marginTop: 8 }}
          >
            Sign Out
          </button>
        </>
      ) : (
        <NavLink
          to="/login"
          className={({ isActive }) =>
            `sidebar__link${isActive ? " sidebar__link--active" : ""}`
          }
        >
          <span className="sidebar__link-dot"></span>
          Sign In
        </NavLink>
      )}
    </aside>
  );
}
