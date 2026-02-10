import { Toaster } from 'react-hot-toast'
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Accounts from './pages/Accounts'
import CalendarPage from './pages/CalendarPage'
import ClipsManager from './pages/ClipsManager'
import Dashboard from './pages/Dashboard'
import InstagramDashboard from './pages/InstagramDashboard'
import LinkedInDashboard from './pages/LinkedInDashboard'
import Login from './pages/Login'
import MediaLibrary from './pages/MediaLibrary'
import OAuthSuccess from './pages/OAuthSuccess'
import PrivacyPolicy from './pages/PrivacyPolicy'
import Register from './pages/Register'
import Schedules from './pages/Schedules'
import SocialScheduler from './pages/SocialScheduler'
import TermsOfService from './pages/TermsOfService'
import YouTubeStudio from './pages/YouTubeStudio'
import { useStore } from './store'

function App() {
  const isAuthenticated = useStore(state => state.isAuthenticated)

  return (
    <Router>
      <Toaster position="top-right" />
      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />}
        />
        <Route
          path="/register"
          element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Register />}
        />
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/oauth/success" element={<OAuthSuccess />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="accounts" element={<Accounts />} />
          <Route path="schedules" element={<Schedules />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="media" element={<MediaLibrary />} />
          <Route path="clips" element={<ClipsManager />} />
          <Route path="social" element={<SocialScheduler />} />
          <Route path="youtube" element={<YouTubeStudio />} />
          <Route path="instagram" element={<InstagramDashboard />} />
          <Route path="linkedin" element={<LinkedInDashboard />} />
        </Route>

        {/* Catch all */}
        <Route path="*" element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />} />
      </Routes>
    </Router>
  )
}

export default App