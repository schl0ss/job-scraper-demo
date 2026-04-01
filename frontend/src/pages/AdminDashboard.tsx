import { useState, useEffect } from 'react'
import { api } from '../api'
import { DashboardStats, Job } from '../types'

type Drilldown = 'available' | 'claimed' | 'submitted' | 'stale' | null

interface SubmissionRow {
  job_code: string
  job_title: string
  employer: string
  location: string
  ra_email: string
  outcome: string
  notes: string
  submitted_at: string
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [markingStale, setMarkingStale] = useState(false)
  const [staleResult, setStaleResult] = useState<string>('')

  const [drilldown, setDrilldown] = useState<Drilldown>(null)
  const [drillJobs, setDrillJobs] = useState<Job[]>([])
  const [drillSubs, setDrillSubs] = useState<SubmissionRow[]>([])
  const [drillLoading, setDrillLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const data = await api.getDashboard()
      setStats(data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleDrilldown = async (key: Drilldown) => {
    if (drilldown === key) { setDrilldown(null); return }
    setDrilldown(key)
    setDrillLoading(true)
    try {
      if (key === 'submitted') {
        const data = await api.listSubmissions()
        setDrillSubs(data)
      } else if (key === 'available' || key === 'claimed') {
        const data = await api.listJobs({ status: key, limit: 200 })
        setDrillJobs(data)
      } else if (key === 'stale') {
        const data = await api.listJobs({ status: 'claimed', limit: 200 })
        setDrillJobs(data)
      }
    } catch {}
    setDrillLoading(false)
  }

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

  if (loading) return <div className="loading">Loading dashboard...</div>
  if (!stats) return null

  const cards: { key: Drilldown; label: string; value: string | number; cls?: string }[] = [
    { key: null, label: 'Total Jobs', value: stats.total_jobs },
    { key: 'available', label: 'Available', value: stats.available },
    { key: 'claimed', label: 'Claimed', value: stats.claimed },
    { key: 'submitted', label: 'Submitted', value: stats.submitted, cls: 'good' },
    { key: 'stale', label: 'Stale Claims', value: stats.stale_claims, cls: stats.stale_claims > 0 ? 'warn' : '' },
    { key: null, label: 'Completion', value: stats.total_jobs > 0 ? `${Math.round((stats.submitted / stats.total_jobs) * 100)}%` : '\u2014' },
  ]

  return (
    <>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Study progress overview</p>
      </div>
      <div className="page-body">
        {/* Stat cards */}
        <div className="stat-grid">
          {cards.map((c, i) => {
            const clickable = c.key !== null
            const active = drilldown !== null && drilldown === c.key
            return (
              <div
                key={i}
                className={`stat-card${clickable ? ' stat-card-clickable' : ''}${active ? ' stat-card-active' : ''}`}
                onClick={clickable ? () => handleDrilldown(c.key) : undefined}
              >
                <div className="stat-label">{c.label}</div>
                <div className={`stat-value ${c.cls || ''}`}>{c.value}</div>
              </div>
            )
          })}
        </div>

        {/* Drilldown table */}
        {drilldown && (
          <div style={{ marginBottom: 28 }}>
            <div className="section-title" style={{ marginBottom: 12 }}>
              {drilldown === 'available' && 'Available Jobs'}
              {drilldown === 'claimed' && 'Claimed Jobs'}
              {drilldown === 'submitted' && 'Submissions'}
              {drilldown === 'stale' && 'Stale Claims'}
            </div>
            {drillLoading ? (
              <div className="loading">Loading...</div>
            ) : drilldown === 'submitted' ? (
              drillSubs.length === 0 ? (
                <div style={{ color: 'var(--text-3)', fontSize: 13 }}>No submissions yet.</div>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Job ID</th>
                        <th>Title</th>
                        <th>Employer</th>
                        <th>RA</th>
                        <th>Outcome</th>
                        <th>Notes</th>
                        <th>Submitted</th>
                      </tr>
                    </thead>
                    <tbody>
                      {drillSubs.map((s, i) => (
                        <tr key={i}>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{s.job_code}</td>
                          <td><div className="td-title">{s.job_title}</div></td>
                          <td><div className="td-sub" style={{ maxWidth: 160 }}>{s.employer}</div></td>
                          <td style={{ fontSize: 12.5 }}>{s.ra_email}</td>
                          <td><span className="badge">{s.outcome}</span></td>
                          <td style={{ fontSize: 12.5, color: 'var(--text-2)', maxWidth: 200 }}>{s.notes || '\u2014'}</td>
                          <td style={{ fontSize: 12, fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                            {s.submitted_at ? new Date(s.submitted_at).toLocaleDateString() : '\u2014'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            ) : (
              drillJobs.length === 0 ? (
                <div style={{ color: 'var(--text-3)', fontSize: 13 }}>No jobs in this category.</div>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Job ID</th>
                        <th>Title</th>
                        <th>Employer</th>
                        <th>Location</th>
                        <th>Edu</th>
                        <th>Posted</th>
                      </tr>
                    </thead>
                    <tbody>
                      {drillJobs.map(job => (
                        <tr key={job.id}>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{job.job_code || job.id}</td>
                          <td><div className="td-title">{job.title}</div></td>
                          <td><div className="td-sub" style={{ maxWidth: 160 }}>{job.employer.canonical_name}</div></td>
                          <td style={{ fontSize: 12.5, whiteSpace: 'nowrap' }}>{job.location.replace(/, TX.*/, ', TX')}</td>
                          <td style={{ fontSize: 12.5 }}>{job.education_level}</td>
                          <td style={{ fontSize: 12, fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>{job.date_posted || '\u2014'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            )}
          </div>
        )}

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
            {markingStale ? 'Running...' : 'Mark stale claims'}
          </button>
          <button className="btn btn-secondary" onClick={() => api.exportCsv()}>
            Export CSV
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
