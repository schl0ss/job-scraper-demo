import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Jobs from './pages/Jobs'
import JobDetail from './pages/JobDetail'
import AdminDashboard from './pages/AdminDashboard'
import AdminIngest from './pages/AdminIngest'
import AdminUsers from './pages/AdminUsers'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { token, role } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  if (role !== 'lead_ra') return <Navigate to="/jobs" replace />
  return <>{children}</>
}

function AppRoutes() {
  const { token } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/jobs" replace /> : <Login />} />

      <Route path="/jobs" element={
        <PrivateRoute>
          <Layout><Jobs /></Layout>
        </PrivateRoute>
      } />

      <Route path="/jobs/:id" element={
        <PrivateRoute>
          <Layout><JobDetail /></Layout>
        </PrivateRoute>
      } />

      <Route path="/admin" element={
        <AdminRoute>
          <Layout><AdminDashboard /></Layout>
        </AdminRoute>
      } />

      <Route path="/admin/ingest" element={
        <AdminRoute>
          <Layout><AdminIngest /></Layout>
        </AdminRoute>
      } />

      <Route path="/admin/users" element={
        <AdminRoute>
          <Layout><AdminUsers /></Layout>
        </AdminRoute>
      } />

      <Route path="*" element={<Navigate to="/jobs" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
