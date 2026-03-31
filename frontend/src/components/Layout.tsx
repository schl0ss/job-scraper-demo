import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, role, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="wordmark">Audit Portal</div>
          <div className="sub">Resume Audit Study</div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">Queue</div>
          <NavLink to="/jobs" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <rect x="1" y="1" width="14" height="3" rx="1" fill="currentColor" opacity=".5"/>
              <rect x="1" y="6.5" width="14" height="3" rx="1" fill="currentColor" opacity=".7"/>
              <rect x="1" y="12" width="14" height="3" rx="1" fill="currentColor"/>
            </svg>
            Job Queue
          </NavLink>

          {role === 'lead_ra' && (
            <>
              <div className="nav-section" style={{ marginTop: 8 }}>Admin</div>
              <NavLink to="/admin" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <rect x="1" y="1" width="6.5" height="6.5" rx="1" fill="currentColor" opacity=".6"/>
                  <rect x="8.5" y="1" width="6.5" height="6.5" rx="1" fill="currentColor"/>
                  <rect x="1" y="8.5" width="6.5" height="6.5" rx="1" fill="currentColor" opacity=".4"/>
                  <rect x="8.5" y="8.5" width="6.5" height="6.5" rx="1" fill="currentColor" opacity=".7"/>
                </svg>
                Dashboard
              </NavLink>
              <NavLink to="/admin/ingest" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <path d="M8 1v10M4 7l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 13h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
                Ingest Jobs
              </NavLink>
              <NavLink to="/admin/users" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="5" r="3" stroke="currentColor" strokeWidth="1.4"/>
                  <path d="M2 14c0-3.314 2.686-5 6-5s6 1.686 6 5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
                </svg>
                Users
              </NavLink>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="user-email">{user?.email || `User #${user?.id}`}</div>
          <div style={{ fontSize: 11, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '.06em' }}>
            {role === 'lead_ra' ? 'Lead RA' : 'Research Assistant'}
          </div>
          <button className="logout-btn" onClick={handleLogout}>Sign out</button>
        </div>
      </aside>

      <main className="main-content">
        {children}
      </main>
    </div>
  )
}
