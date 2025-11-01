import { X } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { clipService } from '../../services/clipService'

export default function CreateClipModal({ media, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    media_id: '',
    start_time: 0,
    end_time: 10,
    title: '',
    description: '',
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async e => {
    e.preventDefault()

    if (!formData.media_id) {
      toast.error('Please select a media file')
      return
    }

    if (formData.start_time >= formData.end_time) {
      toast.error('End time must be greater than start time')
      return
    }

    setLoading(true)
    try {
      await clipService.create({
        ...formData,
        media_id: parseInt(formData.media_id),
      })
      toast.success('Clip created successfully!')
      onSuccess()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create clip')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Create New Clip</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Media File *
            </label>
            <select
              value={formData.media_id}
              onChange={e => setFormData({ ...formData, media_id: e.target.value })}
              className="input"
              required
            >
              <option value="">Choose a file...</option>
              {media.map(item => (
                <option key={item.id} value={item.id}>
                  {item.original_filename} ({item.media_type})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Time (seconds) *
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={formData.start_time}
                onChange={e =>
                  setFormData({ ...formData, start_time: parseFloat(e.target.value) })
                }
                className="input"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Time (seconds) *
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={formData.end_time}
                onChange={e => setFormData({ ...formData, end_time: parseFloat(e.target.value) })}
                className="input"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={e => setFormData({ ...formData, title: e.target.value })}
              className="input"
              placeholder="Optional - AI can generate this"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              className="input"
              rows="3"
              placeholder="Optional - AI can generate this"
            />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              💡 Tip: Leave title and description empty to let AI generate engaging content for
              your clip!
            </p>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? 'Creating...' : 'Create Clip'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}