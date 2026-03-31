import { useState } from 'react'
import { api } from '../api'

export default function AdminUsers() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'ra' | 'lead_ra'>('ra')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const handleCreate = async () => {
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const user: any = await api.createUser(email, password, role)
      setSuccess(`Created ${user.role} account: ${user.email}`)
      setEmail('')
      setPassword('')
    } catch (e: any) {
      setError(e.message)
    }
    setLoading(false)
  }

  return (
    <>
      <div className="page-header">
        <h1>Users</h1>
        <p>Create accounts for research assistants and lead RAs</p>
      </div>
      <div className="page-body">
        <div style={{ maxWidth: 420 }}>
          <div className="card">
            <div className="section-title" style={{ marginBottom: 16 }}>Create new account</div>

            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                className="form-input"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="ra2@university.edu"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                className="form-input"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Temporary password"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Role</label>
              <select
                className="form-select"
                value={role}
                onChange={e => setRole(e.target.value as 'ra' | 'lead_ra')}
              >
                <option value="ra">Research Assistant (RA)</option>
                <option value="lead_ra">Lead RA (admin access)</option>
              </select>
            </div>

            {error && <div className="err-msg" style={{ marginBottom: 12 }}>{error}</div>}
            {success && (
              <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#15803d', padding: '8px 12px', borderRadius: 4, fontSize: 13, marginBottom: 12 }}>
                ✓ {success}
              </div>
            )}

            <button
              className="btn btn-primary"
              onClick={handleCreate}
              disabled={loading || !email || !password}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {loading ? 'Creating…' : 'Create account'}
            </button>
          </div>

          <div style={{ marginTop: 20, padding: '14px 0', borderTop: '1px solid var(--border-lt)', fontSize: 13, color: 'var(--text-2)' }}>
            <strong>Note:</strong> Share credentials directly with RAs. Password reset is not yet implemented — use a temporary password and have the RA contact you to change it.
          </div>
        </div>
      </div>
    </>
  )
}
