import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Job, JobStatus, EducationLevel } from '../types'
import { StatusBadge, EduBadge } from '../components/Badge'

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<string>('')
  const [edu, setEdu] = useState<string>('')
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    try {
      const data = await api.listJobs({
        status: status || undefined,
        education_level: edu || undefined,
        limit: 100,
      })
      setJobs(data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [status, edu])

  return (
    <>
      <div className="page-header">
        <h1>Job Queue</h1>
        <p>Browse and claim job postings for the audit study</p>
      </div>
      <div className="page-body">
        <div className="filters">
          <select className="filter-select" value={status} onChange={e => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="available">Available</option>
            <option value="claimed">Claimed</option>
            <option value="submitted">Submitted</option>
            <option value="excluded">Excluded</option>
          </select>
          <select className="filter-select" value={edu} onChange={e => setEdu(e.target.value)}>
            <option value="">All education levels</option>
            <option value="AA">AA required</option>
            <option value="BA">BA required</option>
            <option value="unspecified">Unspecified</option>
          </select>
          <button className="btn btn-secondary btn-sm" onClick={load}>Refresh</button>
          <span className="filter-count">{jobs.length} jobs</span>
        </div>

        {loading ? (
          <div className="loading">Loading jobs…</div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <p>No jobs match the current filters.</p>
          </div>
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
                  <th>Salary</th>
                  <th>Posted</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr
                    key={job.id}
                    className="tr-link"
                    onClick={() => navigate(`/jobs/${job.id}`)}
                  >
                    <td style={{ color: 'var(--text-3)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                      {job.job_code || job.id}
                    </td>
                    <td>
                      <div className="td-title">{job.title}</div>
                    </td>
                    <td>
                      <div className="td-sub" style={{ maxWidth: 180 }}>{job.employer.canonical_name}</div>
                    </td>
                    <td style={{ fontSize: 12.5, color: 'var(--text-2)', whiteSpace: 'nowrap' }}>
                      {job.location.replace(/, TX.*/, ', TX')}
                    </td>
                    <td><EduBadge level={job.education_level} /></td>
                    <td style={{ fontSize: 12.5, color: 'var(--text-2)', whiteSpace: 'nowrap' }}>
                      {job.salary || <span style={{ color: 'var(--text-3)' }}>—</span>}
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-3)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                      {job.date_posted || '—'}
                    </td>
                    <td><StatusBadge status={job.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}
