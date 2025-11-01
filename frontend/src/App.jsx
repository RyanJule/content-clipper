import { Toaster } from 'react-hot-toast'
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import ClipsManager from './pages/ClipsManager'
import Dashboard from './pages/Dashboard'
import MediaLibrary from './pages/MediaLibrary'
import SocialScheduler from './pages/SocialScheduler'

function App() {
  return (
    <Router>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="media" element={<MediaLibrary />} />
          <Route path="clips" element={<ClipsManager />} />
          <Route path="social" element={<SocialScheduler />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App