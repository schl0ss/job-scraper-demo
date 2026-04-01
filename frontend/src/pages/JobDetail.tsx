import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Job, SubmissionOutcome } from '../types'
import { StatusBadge, EduBadge } from '../components/Badge'

const OUTCOMES: { value: SubmissionOutcome; label: string }[] = [
  { value: 'success', label: 'Submitted successfully' },
  { value: 'expired', label: 'Posting expired / no longer active' },
  { value: 'blocked', label: 'Required SSN or restricted information' },
  { value: 'other', label: 'Other issue (see notes)' },
]

export default function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [claiming, setClaiming] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [outcome, setOutcome] = useState<SubmissionOutcome>('success')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = async () => {
    if (!id) return
    setLoading(true)
    try {
      const data = await api.getJob(Number(id))
      setJob(data)
    } catch {
      setJob(null)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [id])

  const handleClaim = async () => {
    if (!job) return
    setClaiming(true)
    setError('')
    try {
      await api.claimJob(job.id)
      setSuccess('Job claimed — you have 24 hours to submit.')
      await load()
    } catch (e: any) {
      setError(e.message)
    }
    setClaiming(false)
  }

  const handleRelease = async () => {
    if (!job) return
    setClaiming(true)
    setError('')
    try {
      await api.releaseJob(job.id)
      setSuccess('Claim released.')
      await load()
    } catch (e: any) {
      setError(e.message)
    }
    setClaiming(false)
  }

  const handleSubmit = async () => {
    if (!job) return
    setSubmitting(true)
    setError('')
    try {
      await api.submitJob(job.id, outcome, notes)
      setSuccess(`Logged as "${outcome}".`)
      await load()
    } catch (e: any) {
      setError(e.message)
    }
    setSubmitting(false)
  }

  if (loading) return <div className="loading">Loading…</div>
  if (!job) return (
    <div className="page-body">
      <div className="empty-state"><p>Job not found.</p></div>
    </div>
  )

  return (
    <>
      <div className="page-header">
        <Link to="/jobs" className="back-link">← Back to queue</Link>
        <h1 style={{ fontFamily: 'var(--font-mono)', fontSize: 17 }}>{job.title}</h1>
        <div className="job-meta" style={{ marginTop: 8 }}>
          <span>{job.employer.canonical_name}</span>
          <span>{job.location}</span>
          {job.salary && <span>{job.salary}</span>}
          {job.date_posted && <span>Posted {job.date_posted}</span>}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <StatusBadge status={job.status} />
          <EduBadge level={job.education_level} />
        </div>
      </div>

      <div className="page-body">
        <div className="job-grid">
          {/* Description */}
          <div>
            <div className="section-title">Job Description</div>
            {job.source_url && (
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary btn-sm"
                style={{ marginBottom: 12, display: 'inline-flex' }}
              >
                ↗ View original posting
              </a>
            )}
            <div className="description-box">
              {job.description || 'Description not available.'}
            </div>
          </div>

          {/* Action panel */}
          <div className="action-panel">
            <h3>Actions</h3>

            {error && <div className="err-msg" style={{ marginBottom: 12 }}>{error}</div>}
            {success && (
              <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#15803d', padding: '8px 12px', borderRadius: 4, fontSize: 13, marginBottom: 12 }}>
                {success}
              </div>
            )}

            {job.status === 'available' && (
              <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={handleClaim} disabled={claiming}>
                {claiming ? 'Claiming…' : 'Claim this job'}
              </button>
            )}

            {job.status === 'claimed' && (
              <>
                <div className="form-group">
                  <label className="form-label">Outcome</label>
                  <select
                    className="form-select"
                    value={outcome}
                    onChange={e => setOutcome(e.target.value as SubmissionOutcome)}
                  >
                    {OUTCOMES.map(o => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Notes <span style={{ fontWeight: 400, textTransform: 'none' }}>(optional)</span></label>
                  <textarea
                    className="form-textarea"
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="e.g. Applied via Easy Apply, job ID #12345…"
                  />
                </div>
                <button
                  className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center', marginBottom: 8 }}
                  onClick={handleSubmit}
                  disabled={submitting}
                >
                  {submitting ? 'Submitting…' : 'Log submission'}
                </button>
                <hr className="action-divider" />
                <button
                  className="btn btn-danger btn-sm"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={handleRelease}
                  disabled={claiming}
                >
                  Release claim
                </button>
              </>
            )}

            {job.status === 'submitted' && (
              <div style={{ textAlign: 'center', color: 'var(--text-2)', fontSize: 13, padding: '12px 0' }}>
                ✓ Submission logged
              </div>
            )}

            {job.status === 'excluded' && (
              <div style={{ textAlign: 'center', color: 'var(--text-3)', fontSize: 13, padding: '12px 0' }}>
                This posting has been excluded.
              </div>
            )}

            {job.status === 'expired' && (
              <div style={{ textAlign: 'center', color: 'var(--expired-fg)', fontSize: 13, padding: '12px 0' }}>
                This posting has expired.
              </div>
            )}

            <hr className="action-divider" />
            <button
              className="btn btn-ghost btn-sm"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => api.downloadResume(job.id).catch(e => setError(e.message))}
            >
              ↓ Download resume PDF
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
