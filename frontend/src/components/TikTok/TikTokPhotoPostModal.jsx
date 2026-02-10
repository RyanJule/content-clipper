import { ImagePlus, Plus, Trash2, X } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { tiktokService } from '../../services/tiktokService'

export default function TikTokPhotoPostModal({ onClose, onSuccess }) {
  const [photoUrls, setPhotoUrls] = useState([''])
  const [title, setTitle] = useState('')
  const [privacyLevel, setPrivacyLevel] = useState('SELF_ONLY')
  const [disableComment, setDisableComment] = useState(false)
  const [autoAddMusic, setAutoAddMusic] = useState(true)
  const [publishing, setPublishing] = useState(false)

  const addPhotoUrl = () => {
    if (photoUrls.length >= 35) {
      toast.error('Maximum 35 images per photo post')
      return
    }
    setPhotoUrls([...photoUrls, ''])
  }

  const removePhotoUrl = index => {
    if (photoUrls.length <= 1) return
    setPhotoUrls(photoUrls.filter((_, i) => i !== index))
  }

  const updatePhotoUrl = (index, value) => {
    const updated = [...photoUrls]
    updated[index] = value
    setPhotoUrls(updated)
  }

  const handlePublish = async e => {
    e.preventDefault()

    const validUrls = photoUrls.filter(url => url.trim())
    if (validUrls.length === 0) {
      toast.error('Please enter at least one photo URL')
      return
    }

    setPublishing(true)

    try {
      await tiktokService.publishPhotoPost({
        photo_urls: validUrls,
        title: title.trim(),
        privacy_level: privacyLevel,
        disable_comment: disableComment,
        auto_add_music: autoAddMusic,
      })
      onSuccess()
    } catch (error) {
      console.error('Photo post failed:', error)
      toast.error(error.response?.data?.detail || 'Failed to publish photo post.')
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-3">
            <ImagePlus className="w-6 h-6 text-gray-900" />
            <h2 className="text-xl font-bold text-gray-900">Create Photo Post</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" disabled={publishing}>
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handlePublish} className="p-6 space-y-4">
          {/* Photo URLs */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Photo URLs <span className="text-gray-500">(1-35 publicly accessible image URLs)</span>
            </label>
            <div className="space-y-2">
              {photoUrls.map((url, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="url"
                    value={url}
                    onChange={e => updatePhotoUrl(index, e.target.value)}
                    placeholder={`https://example.com/photo${index + 1}.jpg`}
                    className="input flex-1"
                    disabled={publishing}
                  />
                  {photoUrls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removePhotoUrl(index)}
                      className="text-gray-400 hover:text-red-500 p-1"
                      disabled={publishing}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            {photoUrls.length < 35 && (
              <button
                type="button"
                onClick={addPhotoUrl}
                className="mt-2 text-sm text-primary-600 hover:text-primary-700 flex items-center space-x-1"
                disabled={publishing}
              >
                <Plus className="w-4 h-4" />
                <span>Add another photo</span>
              </button>
            )}
            <p className="text-xs text-gray-400 mt-1">
              {photoUrls.filter(u => u.trim()).length}/35 photos
            </p>
          </div>

          {/* Caption */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Caption</label>
            <textarea
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={2200}
              rows={4}
              placeholder="Write a caption for your photo post..."
              className="input"
              disabled={publishing}
            />
            <p className="text-xs text-gray-400 mt-1">{title.length}/2200 characters</p>
          </div>

          {/* Privacy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Privacy</label>
            <select
              value={privacyLevel}
              onChange={e => setPrivacyLevel(e.target.value)}
              className="input"
              disabled={publishing}
            >
              <option value="PUBLIC_TO_EVERYONE">Public</option>
              <option value="MUTUAL_FOLLOW_FRIENDS">Friends</option>
              <option value="FOLLOWER_OF_CREATOR">Followers</option>
              <option value="SELF_ONLY">Only Me</option>
            </select>
          </div>

          {/* Settings */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Settings</label>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="allowCommentPhoto"
                checked={!disableComment}
                onChange={e => setDisableComment(!e.target.checked)}
                className="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
                disabled={publishing}
              />
              <label htmlFor="allowCommentPhoto" className="text-sm text-gray-700">
                Allow comments
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoMusic"
                checked={autoAddMusic}
                onChange={e => setAutoAddMusic(e.target.checked)}
                className="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
                disabled={publishing}
              />
              <label htmlFor="autoMusic" className="text-sm text-gray-700">
                Auto-add background music
              </label>
            </div>
          </div>

          {/* Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              Photo URLs must be publicly accessible. TikTok servers will download the images
              from the provided URLs.
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={publishing}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary bg-gray-900 hover:bg-gray-800"
              disabled={publishing || photoUrls.every(u => !u.trim())}
            >
              {publishing ? 'Publishing...' : 'Publish Photo Post'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
