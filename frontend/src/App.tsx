import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './lib/auth'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { DashboardPage } from './pages/DashboardPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { NewDiscoveryPage } from './pages/NewDiscoveryPage'
import { RunMonitorPage } from './pages/RunMonitorPage'
import { EndpointsPage } from './pages/EndpointsPage'
import { CapturesPage } from './pages/CapturesPage'
import { ClientsPage } from './pages/ClientsPage'
import { SettingsPage } from './pages/SettingsPage'
import { DocumentationPage } from './pages/DocumentationPage'
import { LoadingSpinner } from './components/ui/LoadingSpinner'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/new" element={<NewDiscoveryPage />} />
        <Route path="discover" element={<NewDiscoveryPage />} />
        <Route path="projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="runs" element={<ProjectsPage />} />
        <Route path="runs/:runId" element={<RunMonitorPage />} />
        <Route path="endpoints" element={<EndpointsPage />} />
        <Route path="captures" element={<CapturesPage />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="docs" element={<DocumentationPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}