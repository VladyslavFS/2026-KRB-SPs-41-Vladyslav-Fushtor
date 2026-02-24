export default function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar__logo">
          <div className="sidebar__logo-mark">EQ</div>
          <span className="sidebar__title">Earthquake Platform</span>
        </div>

        <nav className="sidebar__nav">
          <span className="sidebar__section">Monitoring</span>
          <a href="/" className="sidebar__link sidebar__link--active">
            <span className="sidebar__link-dot"></span>
            Feed
          </a>
          <a href="/top-events" className="sidebar__link">
            <span className="sidebar__link-dot"></span>
            Top Events
          </a>

          <span className="sidebar__section">Personal</span>
          <a href="/saved" className="sidebar__link">
            <span className="sidebar__link-dot"></span>
            Saved Events
          </a>
          <a href="/alerts" className="sidebar__link">
            <span className="sidebar__link-dot"></span>
            Alert Rules
          </a>
        </nav>

        <div className="sidebar__divider"></div>
        <a href="/login" className="sidebar__link">
          <span className="sidebar__link-dot"></span>
          Sign In
        </a>
      </aside>

      <main className="main">
        <div className="page-header">
          <h2>Earthquake Feed</h2>
          <p className="page-header__sub">
            Real-time seismic activity monitoring
          </p>
        </div>
        <p className="main__placeholder">
          React + Vite is working. Next commit adds routing and real data.
        </p>
      </main>
    </div>
  );
}
