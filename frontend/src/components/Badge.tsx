import { JobStatus, EducationLevel } from '../types'

export function StatusBadge({ status }: { status: JobStatus }) {
  const labels: Record<JobStatus, string> = {
    available: 'Available',
    claimed: 'Claimed',
    submitted: 'Submitted',
    excluded: 'Excluded',
  }
  return (
    <span className={`badge ${status}`}>
      <span className="badge-dot" />
      {labels[status]}
    </span>
  )
}

export function EduBadge({ level }: { level: EducationLevel }) {
  const labels: Record<EducationLevel, string> = {
    AA: 'AA',
    BA: 'BA',
    unspecified: 'Any',
  }
  const cls = level === 'unspecified' ? 'unspecified' : level.toLowerCase()
  return <span className={`badge ${cls}`}>{labels[level]}</span>
}
