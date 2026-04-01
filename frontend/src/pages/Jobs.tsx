import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Job, JobStatus, EducationLevel } from '../types'
import { StatusBadge, EduBadge } from '../components/Badge'

type SortKey = 'job_code' | 'title' | 'employer' | 'location' | 'education_level' | 'salary' | 'date_posted' | 'status'
type SortDir = 'asc' | 'desc'

const accessors: Record<SortKey, (j: Job) => string | null> = {
  job_code: j => j.job_code,
  title: j => j.title,
  employer: j => j.employer.canonical_name,
  location: j => j.location,
  education_level: j => j.education_level,
  salary: j => j.salary,
  date_posted: j => j.date_posted,
  status: j => j.status,
}

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<string>('')
  const [edu, setEdu] = useState<string>('')
  const [sortKey, setSortKey] = useState<SortKey>('job_code')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const navigate = useNavigate()

  const sortedJobs = useMemo(() => {
    const get = accessors[sortKey]
    return [...jobs].sort((a, b) => {
      const va = get(a)
      const vb = get(b)
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      const cmp = va.localeCompare(vb, undefined, { numeric: true, sensitivity: 'base' })
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [jobs, sortKey, sortDir])

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const SortTh = ({ k, children }: { k: SortKey; children: React.ReactNode }) => (
    <th className="sortable-th" onClick={() => toggleSort(k)}>
      {children}
      <span className="sort-arrow">
        {sortKey === k ? (sortDir === 'asc' ? ' \u25B2' : ' \u25BC') : ' \u25BD'}
      </span>
    </th>
  )

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
                  <SortTh k="job_code">Job ID</SortTh>
                  <SortTh k="title">Title</SortTh>
                  <SortTh k="employer">Employer</SortTh>
                  <SortTh k="location">Location</SortTh>
                  <SortTh k="education_level">Edu</SortTh>
                  <SortTh k="salary">Salary</SortTh>
                  <SortTh k="date_posted">Posted</SortTh>
                  <SortTh k="status">Status</SortTh>
                </tr>
              </thead>
              <tbody>
                {sortedJobs.map(job => (
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
