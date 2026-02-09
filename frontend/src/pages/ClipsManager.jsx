import { Edit2, Play, Plus, Sparkles, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import CreateClipModal from '../components/Clips/CreateClipModal'
import { useApi } from '../hooks/useApi'
import { clipService } from '../services/clipService'
import { mediaService } from '../services/mediaService'
import { useStore } from '../store'
import { formatDateTime, formatDuration } from '../utils/formatters'

export default function ClipsManager() {
  const { clips, setClips, removeClip } = useStore()
  const { loading, execute } = useApi()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [media, setMedia] = useState([])
  const [playerClip, setPlayerClip] = useState(null)
  const [playerUrl, setPlayerUrl] = useState(null)
  const [loadingUrl, setLoadingUrl] = useState(false)

  useEffect(() => {
    loadClips()
    loadMedia()
  }, [])

  const loadClips = async () => {
    execute(
      async () => {
        const data = await clipService.getAll()
        setClips(data)
      },
      { errorMessage: 'Failed to load clips' }
    )
  }

  const loadMedia = async () => {
    try {
      const data = await mediaService.getAll()
      setMedia(data)
    } catch (error) {
      console.error('Failed to load media:', error)
    }
  }

  const handleDelete = async id => {
    if (!confirm('Are you sure you want to delete this clip?')) return

    execute(
      async () => {
        await clipService.delete(id)
        removeClip(id)
      },
      {
        successMessage: 'Clip deleted successfully',
        errorMessage: 'Failed to delete clip',
      }
    )
  }

  const handleGenerateContent = async id => {
    execute(
      async () => {
        await clipService.generateContent(id)
        loadClips()
      },
      {
        successMessage: 'AI content generated!',
        errorMessage: 'Failed to generate content',
      }
    )
  }

  const handlePlay = async clip => {
    setLoadingUrl(true)
    try {
      const data = await clipService.getStreamUrl(clip.id)
      setPlayerClip(clip)
      setPlayerUrl(data.url)
    } catch (error) {
      console.error('Failed to get clip stream URL:', error)
      toast.error('Failed to load clip for playback')
    } finally {
      setLoadingUrl(false)
    }
  }

  const closePlayer = () => {
    setPlayerClip(null)
    setPlayerUrl(null)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Clips Manager</h2>
          <p className="text-gray-600 mt-1">Create and manage video clips</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Create Clip</span>
        </button>
      </div>

      {loading && clips.length === 0 ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading clips...</p>
        </div>
      ) : clips.length === 0 ? (
        <div className="card p-12 text-center">
          <Sparkles className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No clips yet</h3>
          <p className="text-gray-600 mb-6">Create your first clip from uploaded media</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary inline-flex items-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Create Clip</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {clips.map(clip => (
            <div key={clip.id} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => handlePlay(clip)}
                      disabled={loadingUrl || clip.status !== 'ready'}
                      className="w-12 h-12 bg-gradient-to-br from-purple-100 to-purple-200 rounded-lg flex items-center justify-center hover:from-purple-200 hover:to-purple-300 transition-colors disabled:opacity-50"
                      title={clip.status === 'ready' ? 'Play clip' : 'Clip not ready'}
                    >
                      <Play className="w-6 h-6 text-purple-600" />
                    </button>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {clip.title || 'Untitled Clip'}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Duration: {formatDuration(clip.duration)} | {formatDateTime(clip.created_at)}
                      </p>
                    </div>
                  </div>

                  {clip.description && (
                    <p className="mt-3 text-gray-700">{clip.description}</p>
                  )}

                  {clip.hashtags && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {JSON.parse(clip.hashtags).map((tag, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-primary-50 text-primary-600 rounded text-sm"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="mt-3 flex items-center space-x-4 text-sm">
                    <span
                      className={`px-2 py-1 rounded ${
                        clip.status === 'ready'
                          ? 'bg-green-100 text-green-700'
                          : clip.status === 'processing'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {clip.status}
                    </span>
                    <span className="text-gray-600">
                      {clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => handleGenerateContent(clip.id)}
                    className="btn btn-secondary text-sm"
                    title="Generate AI content"
                  >
                    <Sparkles className="w-4 h-4" />
                  </button>
                  <button className="btn btn-secondary text-sm">
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button onClick={() => handleDelete(clip.id)} className="btn btn-danger text-sm">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {playerClip && playerUrl && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {playerClip.title || 'Untitled Clip'}
              </h3>
              <button
                onClick={closePlayer}
                className="p-1 hover:bg-gray-100 rounded-full"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
            <div className="p-4">
              <video
                src={playerUrl}
                controls
                autoPlay
                className="w-full max-h-[70vh] rounded"
              >
                Your browser does not support video playback.
              </video>
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <CreateClipModal
          media={media}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false)
            loadClips()
          }}
        />
      )}
    </div>
  )
}
