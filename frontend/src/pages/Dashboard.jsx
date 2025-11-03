import { Calendar, Scissors, Share2, TrendingUp, Upload, Video } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { clipService } from '../services/clipService'
import { mediaService } from '../services/mediaService'
import { socialService } from '../services/socialService'

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    mediaCount: 0,
    clipsCount: 0,
    postsCount: 0,
    scheduledCount: 0,
  })
  const { loading, execute } = useApi()

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const [media, clips, posts] = await Promise.all([
        mediaService.getAll().catch(() => []),
        clipService.getAll().catch(() => []),
        socialService.getAll().catch(() => []),
      ])

      setStats({
        mediaCount: media.length,
        clipsCount: clips.length,
        postsCount: posts.length,
        scheduledCount: posts.filter(p => p.status === 'scheduled').length,
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const statCards = [
    {
      name: 'Media Files',
      value: stats.mediaCount,
      icon: Video,
      color: 'bg-blue-500',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600',
    },
    {
      name: 'Generated Clips',
      value: stats.clipsCount,
      icon: Scissors,
      color: 'bg-purple-500',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600',
    },
    {
      name: 'Social Posts',
      value: stats.postsCount,
      icon: Share2,
      color: 'bg-green-500',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600',
    },
    {
      name: 'Scheduled',
      value: stats.scheduledCount,
      icon: TrendingUp,
      color: 'bg-orange-500',
      bgColor: 'bg-orange-50',
      textColor: 'text-orange-600',
    },
  ]

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-600 mt-1">Overview of your content pipeline</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map(stat => (
          <div key={stat.name} className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">{stat.name}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
              </div>
              <div className={`${stat.bgColor} p-3 rounded-lg`}>
                <stat.icon className={`w-6 h-6 ${stat.textColor}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/media')}
            className="btn btn-primary flex items-center justify-center space-x-2"
          >
            <Upload className="w-5 h-5" />
            <span>Upload Media</span>
          </button>
          <button
            onClick={() => navigate('/clips')}
            className="btn btn-secondary flex items-center justify-center space-x-2"
          >
            <Scissors className="w-5 h-5" />
            <span>Create Clip</span>
          </button>
          <button
            onClick={() => navigate('/social')}
            className="btn btn-secondary flex items-center justify-center space-x-2"
          >
            <Calendar className="w-5 h-5" />
            <span>Schedule Post</span>
          </button>
        </div>
      </div>

      {/* API Connection Test */}
      <div className="card p-6 mt-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">System Health</h3>
        <button
          onClick={async () => {
            try {
              const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/health/`)
              const data = await response.json()
              console.log('Health check:', data)
              toast.success(`API Status: ${data.status}`)
            } catch (error) {
              console.error('Health check failed:', error)
              toast.error('Failed to connect to API')
            }
          }}
          className="btn btn-secondary"
        >
          Test API Connection
        </button>
      </div>

      {/* Getting Started Guide */}
      <div className="card p-6 mt-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Getting Started</h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-bold flex-shrink-0">
              1
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Upload Your Content</h4>
              <p className="text-sm text-gray-600">
                Start by uploading video or audio files to your media library
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-bold flex-shrink-0">
              2
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Generate Clips</h4>
              <p className="text-sm text-gray-600">
                AI will transcribe and suggest interesting moments to clip
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-bold flex-shrink-0">
              3
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Schedule & Publish</h4>
              <p className="text-sm text-gray-600">
                Schedule your clips to be published across social media platforms
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}