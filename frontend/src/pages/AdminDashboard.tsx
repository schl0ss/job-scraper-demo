import { useState, useEffect } from 'react'
import { api } from '../api'
import { DashboardStats } from '../types'

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [markingStale, setMarkingStale] = useState(false)
  const [staleResult, setStaleResult] = useState<string>('')

  const load = async () => {
    setLoading(true)
    try {
      const data = await api.getDashboard()
      setStats(data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleMarkStale = async () => {
    setMarkingStale(true)
    try {
      const res = await api.markStale()
      setStaleResult(`${res.marked_stale} claims marked stale.`)
      await load()
    } catch (e: any) {
      setStaleResult(e.message)
    }
    setMarkingStale(false)
  }

  if (loading) return <div className="loading">Loading dashboard…</div>
  if (!stats) return null

  return (
    <>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Study progress overview</p>
      </div>
      <div className="page-body">
        {/* Stat cards */}
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-label">Total Jobs</div>
            <div className="stat-value">{stats.total_jobs}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Available</div>
            <div className="stat-value">{stats.available}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Claimed</div>
            <div className="stat-value">{stats.claimed}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Submitted</div>
            <div className="stat-value good">{stats.submitted}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Stale Claims</div>
            <div className={`stat-value ${stats.stale_claims > 0 ? 'warn' : ''}`}>
              {stats.stale_claims}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Completion</div>
            <div className="stat-value">
              {stats.total_jobs > 0
                ? `${Math.round((stats.submitted / stats.total_jobs) * 100)}%`
                : '—'}
            </div>
          </div>
        </div>

        {/* Per-RA breakdown */}
        <div className="section-title" style={{ marginBottom: 12 }}>RA Activity</div>
        {stats.per_ra.length === 0 ? (
          <div style={{ color: 'var(--text-3)', fontSize: 13 }}>No research assistants yet.</div>
        ) : (
          <div className="table-wrap" style={{ marginBottom: 28 }}>
            <table>
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Claimed</th>
                  <th>Submitted</th>
                  <th>Stale</th>
                  <th>Progress</th>
                </tr>
              </thead>
              <tbody>
                {stats.per_ra.map(row => {
                  const total = row.claimed + row.submitted
                  const pct = total > 0 ? Math.round((row.submitted / total) * 100) : 0
                  return (
                    <tr key={row.ra.id}>
                      <td style={{ fontWeight: 500 }}>{row.ra.email}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{row.claimed}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--submitted-fg)' }}>{row.submitted}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: row.stale > 0 ? 'var(--claimed-fg)' : 'var(--text-3)' }}>
                        {row.stale}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{
                            width: 80, height: 4, background: 'var(--border)',
                            borderRadius: 2, overflow: 'hidden',
                          }}>
                            <div style={{ width: `${pct}%`, height: '100%', background: 'var(--submitted-dot)', borderRadius: 2 }} />
                          </div>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--text-2)' }}>
                            {pct}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Actions */}
        <div className="section-title" style={{ marginBottom: 12 }}>Admin Actions</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <button className="btn btn-secondary" onClick={handleMarkStale} disabled={markingStale}>
            {markingStale ? 'Running…' : 'Mark stale claims'}
          </button>
          <button className="btn btn-secondary" onClick={() => api.exportCsv()}>
            ↓ Export CSV
          </button>
          <button className="btn btn-ghost btn-sm" onClick={load}>Refresh</button>
          {staleResult && (
            <span style={{ fontSize: 13, color: 'var(--text-2)' }}>{staleResult}</span>
          )}
        </div>
      </div>
    </>
  )
}
