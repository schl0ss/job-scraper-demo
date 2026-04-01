export type UserRole = 'ra' | 'lead_ra'
export type JobStatus = 'available' | 'claimed' | 'submitted' | 'excluded'
export type EducationLevel = 'AA' | 'BA' | 'unspecified'
export type SubmissionOutcome = 'applied' | 'no_response' | 'rejected' | 'not_qualified' | 'duplicate' | 'no_longer_accepting'

export interface User {
  id: number
  email: string
  role: UserRole
}

export interface Employer {
  id: number
  canonical_name: string
  metro: string
}

export interface Job {
  id: number
  job_code: string | null
  title: string
  employer: Employer
  location: string
  education_level: EducationLevel
  salary: string | null
  source_url: string | null
  date_posted: string | null
  status: JobStatus
  created_at: string
  description?: string
}

export interface Assignment {
  assignment_id: number
  claimed_at: string
}

export interface Submission {
  id: number
  job_id: number
  ra_user_id: number
  outcome: SubmissionOutcome
  submitted_at: string
  notes: string | null
}

export interface RAStats {
  ra: User
  claimed: number
  submitted: number
  stale: number
}

export interface DashboardStats {
  total_jobs: number
  available: number
  claimed: number
  submitted: number
  excluded: number
  stale_claims: number
  per_ra: RAStats[]
}

export interface IngestionResult {
  fetched: number
  inserted: number
  skipped_duplicates: number
  review_queue_additions: number
}
