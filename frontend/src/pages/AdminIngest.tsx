import { useState } from 'react'
import { api } from '../api'
import { IngestionResult } from '../types'

export default function AdminIngest() {
  const [limit, setLimit] = useState('25')
  const [jobTitles, setJobTitles] = useState('registered nurse, RN, nurse')
  const [locationPattern, setLocationPattern] = useState('Dallas|Fort Worth|Plano|Frisco|Arlington|McKinney|Irving')
  const [maxAge, setMaxAge] = useState('7')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<IngestionResult | null>(null)
  const [error, setError] = useState('')

  const handleIngest = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const body: any = {
        limit: Number(limit),
        max_age_days: Number(maxAge),
      }
      if (jobTitles.trim()) {
        body.job_titles = jobTitles.split(',').map(s => s.trim()).filter(Boolean)
      }
      if (locationPattern.trim()) {
        body.location_pattern = locationPattern.trim()
      }
      const res = await api.triggerIngestion(body)
      setResult(res)
    } catch (e: any) {
      setError(e.message)
    }
    setLoading(false)
  }

  return (
    <>
      <div className="page-header">
        <h1>Ingest Jobs</h1>
        <p>Fetch new job postings from TheirStack into the queue</p>
      </div>
      <div className="page-body">
        <div style={{ maxWidth: 520 }}>
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="form-group">
              <label className="form-label">Job Titles</label>
              <input
                className="form-input"
                value={jobTitles}
                onChange={e => setJobTitles(e.target.value)}
                placeholder="registered nurse, RN, nurse"
              />
              <div className="form-hint">Comma-separated search terms</div>
            </div>

            <div className="form-group">
              <label className="form-label">Location Pattern</label>
              <input
                className="form-input"
                value={locationPattern}
                onChange={e => setLocationPattern(e.target.value)}
                placeholder="Dallas|Fort Worth|Plano"
              />
              <div className="form-hint">Regex OR pattern for metro area cities</div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div className="form-group">
                <label className="form-label">Max Results</label>
                <input
                  className="form-input"
                  type="number"
                  min={1}
                  max={500}
                  value={limit}
                  onChange={e => setLimit(e.target.value)}
                />
                <div className="form-hint">1 API credit per result</div>
              </div>
              <div className="form-group">
                <label className="form-label">Max Age (days)</label>
                <input
                  className="form-input"
                  type="number"
                  min={1}
                  max={30}
                  value={maxAge}
                  onChange={e => setMaxAge(e.target.value)}
                />
                <div className="form-hint">Only postings this recent</div>
              </div>
            </div>

            {error && <div className="err-msg" style={{ marginBottom: 12 }}>{error}</div>}

            <button
              className="btn btn-primary"
              onClick={handleIngest}
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {loading ? 'Fetching…' : 'Run ingestion'}
            </button>
          </div>

          {result && (
            <div className="result-box">
              <div className="result-title">Ingestion complete</div>
              <div className="result-row"><span>Fetched from API</span><span className="val">{result.fetched}</span></div>
              <div className="result-row"><span>Inserted (new)</span><span className="val">{result.inserted}</span></div>
              <div className="result-row"><span>Skipped (duplicates)</span><span className="val">{result.skipped_duplicates}</span></div>
              <div className="result-row"><span>Dedup review items</span><span className="val">{result.review_queue_additions}</span></div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
