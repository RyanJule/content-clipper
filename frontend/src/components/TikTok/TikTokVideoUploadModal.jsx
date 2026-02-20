import { AlertCircle, Loader, Upload, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { tiktokService } from '../../services/tiktokService'

const PRIVACY_LABELS = {
  PUBLIC_TO_EVERYONE: 'Public',
  MUTUAL_FOLLOW_FRIENDS: 'Friends',
  FOLLOWER_OF_CREATOR: 'Followers',
  SELF_ONLY: 'Private (only me)',
}

export default function TikTokVideoUploadModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef(null)

  // Creator info — required by TikTok before every publish to validate
  // posting constraints and privacy options.
  // Skipping this step causes a 403 "Please review our integration guidelines".
  const [creatorInfo, setCreatorInfo] = useState(null)
  const [creatorLoading, setCreatorLoading] = useState(true)
  const [creatorError, setCreatorError] = useState(null)

  // Post metadata (all required by TikTok Content Sharing Guidelines)
  const [title, setTitle] = useState('')
  const [privacyLevel, setPrivacyLevel] = useState('')
  const [disableDuet, setDisableDuet] = useState(false)
  const [disableComment, setDisableComment] = useState(false)
  const [disableStitch, setDisableStitch] = useState(false)
  const [brandContentToggle, setBrandContentToggle] = useState(false)
  const [brandOrganicToggle, setBrandOrganicToggle] = useState(false)

  useEffect(() => {
    const fetchCreatorInfo = async () => {
      try {
        const info = await tiktokService.getCreatorInfo()
        setCreatorInfo(info)
        // Default to first allowed privacy option (no hardcoded defaults per guidelines)
        if (info.privacy_level_options?.length > 0) {
          setPrivacyLevel(info.privacy_level_options[0])
        }
        // Respect creator-level interaction locks returned by the API
        if (info.duet_disabled) setDisableDuet(true)
        if (info.comment_disabled) setDisableComment(true)
        if (info.stitch_disabled) setDisableStitch(true)
      } catch (err) {
        setCreatorError(
          err.response?.data?.detail ||
            'Failed to load creator info. Please reconnect your TikTok account.',
        )
      } finally {
        setCreatorLoading(false)
      }
    }
    fetchCreatorInfo()
  }, [])

  const handleFileSelect = e => {
    const selected = e.target.files[0]
    if (!selected) return

    if (!selected.type.startsWith('video/')) {
      toast.error('Please select a video file')
      return
    }

    if (selected.size > 4 * 1024 * 1024 * 1024) {
      toast.error('Video file must be under 4GB')
      return
    }

    setFile(selected)
  }

  const handleBrandToggle = (field, checked) => {
    if (field === 'content') setBrandContentToggle(checked)
    else setBrandOrganicToggle(checked)

    // Branded content cannot be private — update privacy level if needed
    if (checked && privacyLevel === 'SELF_ONLY') {
      const nonPrivate = (creatorInfo?.privacy_level_options ?? []).find(o => o !== 'SELF_ONLY')
      if (nonPrivate) setPrivacyLevel(nonPrivate)
    }
  }

  const handleUpload = async e => {
    e.preventDefault()

    if (!file) {
      toast.error('Please select a video file')
      return
    }

    if (!title.trim()) {
      toast.error('A post title is required')
      return
    }

    if (!privacyLevel) {
      toast.error('Please select a privacy level')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const metadata = {
        title: title.trim(),
        privacy_level: privacyLevel,
        disable_duet: disableDuet,
        disable_comment: disableComment,
        disable_stitch: disableStitch,
        brand_content_toggle: brandContentToggle,
        brand_organic_toggle: brandOrganicToggle,
      }

      const onProgress = percent => {
        setUploadProgress(percent)
      }

      await tiktokService.uploadVideo(file, metadata, onProgress)
      toast.success('Video published to TikTok!')
      onSuccess()
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error(error.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = bytes => {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
    return (bytes / 1024).toFixed(1) + ' KB'
  }

  const privacyOptions = creatorInfo?.privacy_level_options ?? []
  const brandedContentActive = brandContentToggle || brandOrganicToggle

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-3">
            <Upload className="w-6 h-6 text-gray-900" />
            <h2 className="text-xl font-bold text-gray-900">Upload TikTok Video</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" disabled={uploading}>
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Creator info header — required: display creator nickname per guidelines */}
        {creatorLoading && (
          <div className="px-6 pt-4 flex items-center space-x-2 text-sm text-gray-500">
            <Loader className="w-4 h-4 animate-spin" />
            <span>Loading creator info…</span>
          </div>
        )}
        {creatorError && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
            <p className="text-sm text-red-700">{creatorError}</p>
          </div>
        )}
        {!creatorLoading && !creatorError && creatorInfo && (
          <div className="px-6 pt-4 flex items-center space-x-2 text-sm text-gray-600">
            {creatorInfo.creator_avatar_url && (
              <img
                src={creatorInfo.creator_avatar_url}
                alt="Creator avatar"
                className="w-6 h-6 rounded-full"
              />
            )}
            <span>
              Posting as{' '}
              <span className="font-medium text-gray-900">
                {creatorInfo.creator_nickname ?? creatorInfo.display_name ?? 'Unknown'}
              </span>
            </span>
          </div>
        )}

        <form onSubmit={handleUpload} className="p-6 space-y-4">
          {/* File Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Video File <span className="text-gray-500">(max 4GB, 1s-10min)</span>
            </label>
            <input
              type="file"
              ref={fileInputRef}
              accept="video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            {file ? (
              <div className="border border-gray-300 rounded-lg p-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  className="text-gray-400 hover:text-red-500"
                  disabled={uploading}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors"
              >
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Click to select a video file</p>
                <p className="text-xs text-gray-400 mt-1">MP4, MOV, WebM supported</p>
              </button>
            )}
          </div>

          {/* Caption / Title — required per TikTok Content Sharing Guidelines */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Caption / Title <span className="text-red-500">*</span>
            </label>
            <textarea
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={2200}
              rows={3}
              placeholder="Write a caption for your video…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 resize-none"
              disabled={uploading}
            />
            <p className="text-xs text-gray-400 mt-1 text-right">{title.length}/2200</p>
          </div>

          {/* Privacy Level — required user-chosen dropdown per guidelines (no hardcoded defaults) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Who can view this post <span className="text-red-500">*</span>
            </label>
            {privacyOptions.length > 0 ? (
              <select
                value={privacyLevel}
                onChange={e => setPrivacyLevel(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                disabled={uploading}
              >
                {privacyOptions.map(opt => (
                  <option key={opt} value={opt}>
                    {PRIVACY_LABELS[opt] ?? opt}
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-sm text-gray-400 italic">Loading privacy options…</p>
            )}
            {brandedContentActive && privacyLevel === 'SELF_ONLY' && (
              <p className="mt-1 text-xs text-amber-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Branded content cannot be posted as Private.</span>
              </p>
            )}
          </div>

          {/* Interaction Settings */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Allow viewers to</p>
            <div className="space-y-2">
              {[
                { label: 'Duet', field: 'duet', locked: creatorInfo?.duet_disabled, value: !disableDuet, set: v => setDisableDuet(!v) },
                { label: 'Comment', field: 'comment', locked: creatorInfo?.comment_disabled, value: !disableComment, set: v => setDisableComment(!v) },
                { label: 'Stitch', field: 'stitch', locked: creatorInfo?.stitch_disabled, value: !disableStitch, set: v => setDisableStitch(!v) },
              ].map(({ label, field, locked, value, set }) => (
                <label key={field} className="flex items-center space-x-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={value}
                    onChange={e => set(e.target.checked)}
                    disabled={uploading || locked}
                    className="rounded"
                  />
                  <span className={locked ? 'text-gray-400' : ''}>
                    {label}
                    {locked && ' (disabled by your account settings)'}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Commercial Content Disclosure — required per TikTok Content Sharing Guidelines */}
          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            <p className="text-sm font-medium text-gray-700">Commercial Content Disclosure</p>
            <p className="text-xs text-gray-500">
              Disclose if this content promotes a brand, product, or service.
            </p>
            <label className="flex items-start space-x-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={brandContentToggle}
                onChange={e => handleBrandToggle('content', e.target.checked)}
                disabled={uploading}
                className="rounded mt-0.5"
              />
              <span>Your brand — you are promoting yourself or your own business</span>
            </label>
            <label className="flex items-start space-x-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={brandOrganicToggle}
                onChange={e => handleBrandToggle('organic', e.target.checked)}
                disabled={uploading}
                className="rounded mt-0.5"
              />
              <span>Branded content — you are promoting another brand or a third party</span>
            </label>
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div>
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>Uploading video...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-gray-900 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary bg-gray-900 hover:bg-gray-800"
              disabled={uploading || !file || creatorLoading || !!creatorError || !privacyLevel}
            >
              {uploading ? 'Publishing...' : 'Publish Video'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
