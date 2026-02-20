import { AlertCircle, CheckCircle, Clock, Loader, Upload, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { tiktokService } from '../../services/tiktokService'

const PRIVACY_LABELS = {
  PUBLIC_TO_EVERYONE: 'Public',
  MUTUAL_FOLLOW_FRIENDS: 'Friends',
  FOLLOWER_OF_CREATOR: 'Followers',
  SELF_ONLY: 'Private (only me)',
}

const POLL_INTERVAL_MS = 3000
const MAX_POLL_ATTEMPTS = 40

export default function TikTokVideoUploadModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null)
  const [videoPreviewUrl, setVideoPreviewUrl] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [publishId, setPublishId] = useState(null)
  // 'polling' | 'done' | 'failed' | null
  const [publishStatus, setPublishStatus] = useState(null)
  const fileInputRef = useRef(null)

  // Creator info — required by TikTok before every publish to validate
  // posting constraints and privacy options.
  const [creatorInfo, setCreatorInfo] = useState(null)
  const [creatorLoading, setCreatorLoading] = useState(true)
  const [creatorError, setCreatorError] = useState(null)

  // Post metadata (all required by TikTok Content Sharing Guidelines)
  const [title, setTitle] = useState('')
  // No default privacy — guidelines require user to manually select ("no default value")
  const [privacyLevel, setPrivacyLevel] = useState('')
  // Interaction settings: all disabled by default — guidelines: "none should be checked by default"
  const [disableDuet, setDisableDuet] = useState(true)
  const [disableComment, setDisableComment] = useState(true)
  const [disableStitch, setDisableStitch] = useState(true)

  // Commercial content disclosure (guidelines require a parent toggle, off by default)
  const [contentDisclosureEnabled, setContentDisclosureEnabled] = useState(false)
  // "Your brand" — promoting yourself/own business → brand_organic_toggle
  const [brandOrganicToggle, setBrandOrganicToggle] = useState(false)
  // "Branded content" — promoting a third party → brand_content_toggle
  const [brandContentToggle, setBrandContentToggle] = useState(false)

  const [durationError, setDurationError] = useState(null)

  useEffect(() => {
    const fetchCreatorInfo = async () => {
      try {
        const info = await tiktokService.getCreatorInfo()
        setCreatorInfo(info)
        // Respect creator-level interaction locks returned by the API.
        // Do NOT pre-select privacy — guidelines require the user to choose manually.
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

  // Revoke the preview object URL on unmount to avoid memory leaks.
  useEffect(() => {
    return () => {
      if (videoPreviewUrl) URL.revokeObjectURL(videoPreviewUrl)
    }
  }, [videoPreviewUrl])

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

    // Revoke previous preview URL before creating a new one.
    if (videoPreviewUrl) URL.revokeObjectURL(videoPreviewUrl)
    const previewUrl = URL.createObjectURL(selected)
    setVideoPreviewUrl(previewUrl)
    setDurationError(null)

    // Validate duration against creator's max_video_post_duration_sec (guideline §1c).
    const maxSec = creatorInfo?.max_video_post_duration_sec
    if (maxSec) {
      const video = document.createElement('video')
      video.preload = 'metadata'
      video.onloadedmetadata = () => {
        if (video.duration > maxSec) {
          setDurationError(
            `Video is ${Math.round(video.duration)}s but your TikTok account allows a maximum of ${maxSec}s.`,
          )
          setFile(null)
          URL.revokeObjectURL(previewUrl)
          setVideoPreviewUrl(null)
          if (fileInputRef.current) fileInputRef.current.value = ''
        } else {
          setFile(selected)
        }
      }
      video.src = previewUrl
    } else {
      setFile(selected)
    }
  }

  const handlePrivacyChange = value => {
    // Branded content (third-party) cannot be set to private — guard at the option level too.
    if (value === 'SELF_ONLY' && brandContentToggle && contentDisclosureEnabled) return
    setPrivacyLevel(value)
  }

  const handleContentDisclosureToggle = checked => {
    setContentDisclosureEnabled(checked)
    if (!checked) {
      setBrandOrganicToggle(false)
      setBrandContentToggle(false)
    }
  }

  // When "Branded content" (third-party) is toggled on, SELF_ONLY is not allowed.
  const handleBrandContentToggle = checked => {
    setBrandContentToggle(checked)
    if (checked && privacyLevel === 'SELF_ONLY') {
      const nonPrivate = (creatorInfo?.privacy_level_options ?? []).find(o => o !== 'SELF_ONLY')
      if (nonPrivate) setPrivacyLevel(nonPrivate)
    }
  }

  // Poll publish/status/fetch until complete or failed (guideline §5e).
  const pollPublishStatus = async id => {
    setPublishStatus('polling')
    for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
      await new Promise(r => setTimeout(r, POLL_INTERVAL_MS))
      try {
        const data = await tiktokService.getPublishStatus(id)
        const st = data.status
        if (st === 'PUBLISH_COMPLETE') {
          setPublishStatus('done')
          return
        }
        if (st === 'FAILED') {
          setPublishStatus('failed')
          toast.error(`TikTok publish failed: ${data.fail_reason ?? 'Unknown error'}`)
          return
        }
      } catch {
        // Network hiccup — continue polling.
      }
    }
    // Timed out but upload was accepted; treat as done.
    setPublishStatus('done')
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
    if (contentDisclosureEnabled && !brandOrganicToggle && !brandContentToggle) {
      toast.error('Please indicate if your content promotes yourself, a third party, or both')
      return
    }
    if (durationError) {
      toast.error(durationError)
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
        brand_content_toggle: contentDisclosureEnabled && brandContentToggle,
        brand_organic_toggle: contentDisclosureEnabled && brandOrganicToggle,
      }

      const onProgress = percent => setUploadProgress(percent)

      const result = await tiktokService.uploadVideo(file, metadata, onProgress)
      setPublishId(result.publish_id)
      setUploading(false)

      // Start polling publish status so users see processing progress (guideline §5d, §5e).
      pollPublishStatus(result.publish_id)

      onSuccess()
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error(error.response?.data?.detail || 'Upload failed. Please try again.')
      setUploading(false)
    }
  }

  const formatFileSize = bytes => {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
    return (bytes / 1024).toFixed(1) + ' KB'
  }

  const privacyOptions = creatorInfo?.privacy_level_options ?? []

  // Consent declaration text — changes based on commercial content selection (guideline §4).
  const disclosureDeclaration =
    contentDisclosureEnabled && brandContentToggle
      ? "By posting, you agree to TikTok's Branded Content Policy and Music Usage Confirmation."
      : "By posting, you agree to TikTok's Music Usage Confirmation."

  const publishDisabled =
    uploading ||
    !file ||
    creatorLoading ||
    !!creatorError ||
    !privacyLevel ||
    !!durationError ||
    (contentDisclosureEnabled && !brandOrganicToggle && !brandContentToggle)

  // ==================== Post-upload processing screens ====================

  if (publishStatus === 'done' || publishStatus === 'failed') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg w-full max-w-md p-8 text-center space-y-4">
          {publishStatus === 'done' ? (
            <>
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto" />
              <h2 className="text-xl font-bold text-gray-900">Video Published!</h2>
              {/* Processing time notice — required by guideline §5d */}
              <p className="text-sm text-gray-600">
                Your video is being processed by TikTok. It may take a few minutes before it
                becomes visible on your profile.
              </p>
            </>
          ) : (
            <>
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
              <h2 className="text-xl font-bold text-gray-900">Publish Failed</h2>
              <p className="text-sm text-gray-600">
                TikTok was unable to process your video. Please try again.
              </p>
            </>
          )}
          <button onClick={onClose} className="btn btn-primary bg-gray-900 hover:bg-gray-800">
            Close
          </button>
        </div>
      </div>
    )
  }

  if (publishStatus === 'polling') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg w-full max-w-md p-8 text-center space-y-4">
          <Clock className="w-12 h-12 text-gray-400 mx-auto" />
          <h2 className="text-xl font-bold text-gray-900">Processing…</h2>
          {/* Processing time notice — required by guideline §5d */}
          <p className="text-sm text-gray-600">
            TikTok is processing your video. This may take a few minutes before it appears on your
            profile.
          </p>
          <Loader className="w-6 h-6 text-gray-400 animate-spin mx-auto" />
        </div>
      </div>
    )
  }

  // ==================== Upload form ====================

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

        {/* Creator info header — required: display creator nickname (guideline §1a) */}
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
          {/* File Selection + Preview (guideline §5a) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Video File{' '}
              <span className="text-gray-500">
                (max 4GB
                {creatorInfo?.max_video_post_duration_sec
                  ? `, max ${creatorInfo.max_video_post_duration_sec}s`
                  : ''}
                )
              </span>
            </label>
            <input
              type="file"
              ref={fileInputRef}
              accept="video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            {file ? (
              <div className="space-y-2">
                <div className="border border-gray-300 rounded-lg p-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setFile(null)
                      if (videoPreviewUrl) {
                        URL.revokeObjectURL(videoPreviewUrl)
                        setVideoPreviewUrl(null)
                      }
                      setDurationError(null)
                      if (fileInputRef.current) fileInputRef.current.value = ''
                    }}
                    className="text-gray-400 hover:text-red-500"
                    disabled={uploading}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                {/* Video preview — guideline §5a */}
                {videoPreviewUrl && (
                  <video
                    src={videoPreviewUrl}
                    controls
                    className="w-full rounded-lg max-h-48 bg-black"
                  />
                )}
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
            {durationError && (
              <p className="mt-1 text-xs text-red-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{durationError}</span>
              </p>
            )}
          </div>

          {/* Caption / Title — required per guideline §2a */}
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

          {/* Privacy Level — user must manually select, no default (guideline §2b) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Who can view this post <span className="text-red-500">*</span>
            </label>
            {privacyOptions.length > 0 ? (
              <select
                value={privacyLevel}
                onChange={e => handlePrivacyChange(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                disabled={uploading}
              >
                <option value="" disabled>
                  Select who can view…
                </option>
                {privacyOptions.map(opt => {
                  const blockedByBrandedContent =
                    opt === 'SELF_ONLY' && brandContentToggle && contentDisclosureEnabled
                  return (
                    <option key={opt} value={opt} disabled={blockedByBrandedContent}>
                      {PRIVACY_LABELS[opt] ?? opt}
                      {blockedByBrandedContent ? ' (unavailable for branded content)' : ''}
                    </option>
                  )
                })}
              </select>
            ) : (
              <p className="text-sm text-gray-400 italic">Loading privacy options…</p>
            )}
            {brandContentToggle && contentDisclosureEnabled && privacyLevel === 'SELF_ONLY' && (
              <p className="mt-1 text-xs text-amber-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Branded content visibility cannot be set to private.</span>
              </p>
            )}
          </div>

          {/* Interaction Settings — none checked by default (guideline §2c) */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Allow viewers to</p>
            <div className="space-y-2">
              {[
                {
                  label: 'Comment',
                  field: 'comment',
                  locked: creatorInfo?.comment_disabled,
                  value: !disableComment,
                  set: v => setDisableComment(!v),
                },
                {
                  label: 'Duet',
                  field: 'duet',
                  locked: creatorInfo?.duet_disabled,
                  value: !disableDuet,
                  set: v => setDisableDuet(!v),
                },
                {
                  label: 'Stitch',
                  field: 'stitch',
                  locked: creatorInfo?.stitch_disabled,
                  value: !disableStitch,
                  set: v => setDisableStitch(!v),
                },
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

          {/* Commercial Content Disclosure — parent toggle required by guideline §3a */}
          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-gray-700">Content Disclosure</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Indicate if this content promotes yourself, a brand, product, or service.
                </p>
              </div>
              {/* Toggle switch */}
              <button
                type="button"
                role="switch"
                aria-checked={contentDisclosureEnabled}
                onClick={() => handleContentDisclosureToggle(!contentDisclosureEnabled)}
                disabled={uploading}
                className={`relative mt-0.5 inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors focus:outline-none ${
                  contentDisclosureEnabled ? 'bg-gray-900' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                    contentDisclosureEnabled ? 'translate-x-4' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>

            {/* Sub-checkboxes only shown when toggle is on (guideline §3a) */}
            {contentDisclosureEnabled && (
              <div className="space-y-2 pt-1 border-t border-gray-100">
                {/* "Your brand" → brand_organic_toggle */}
                <label className="flex items-start space-x-2 text-sm text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={brandOrganicToggle}
                    onChange={e => setBrandOrganicToggle(e.target.checked)}
                    disabled={uploading}
                    className="rounded mt-0.5"
                  />
                  <span>
                    <span className="font-medium">Your brand</span> — you are promoting yourself or
                    your own business
                    {brandOrganicToggle && (
                      <span className="block text-xs text-amber-700 mt-0.5">
                        Your video will be labeled as &ldquo;Promotional content&rdquo;
                      </span>
                    )}
                  </span>
                </label>

                {/* "Branded content" (third-party) → brand_content_toggle */}
                <label className="flex items-start space-x-2 text-sm text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={brandContentToggle}
                    onChange={e => handleBrandContentToggle(e.target.checked)}
                    disabled={uploading}
                    className="rounded mt-0.5"
                  />
                  <span>
                    <span className="font-medium">Branded content</span> — you are promoting another
                    brand or a third party
                    {brandContentToggle && (
                      <span className="block text-xs text-amber-700 mt-0.5">
                        Your video will be labeled as &ldquo;Paid partnership&rdquo;
                      </span>
                    )}
                  </span>
                </label>

                {/* Validation hint when toggle is on but nothing selected (guideline §3a) */}
                {!brandOrganicToggle && !brandContentToggle && (
                  <p className="text-xs text-red-600 flex items-center space-x-1">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>
                      You need to indicate if your content promotes yourself, a third party, or
                      both.
                    </span>
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div>
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>Uploading video…</span>
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

          {/* Consent declaration — required by guideline §4, text changes with branded content */}
          <p className="text-xs text-gray-500 leading-relaxed">{disclosureDeclaration}</p>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-2">
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
              className="btn btn-primary bg-gray-900 hover:bg-gray-800 disabled:opacity-50"
              disabled={publishDisabled}
              title={
                contentDisclosureEnabled && !brandOrganicToggle && !brandContentToggle
                  ? 'You need to indicate if your content promotes yourself, a third party, or both.'
                  : undefined
              }
            >
              {uploading ? 'Publishing…' : 'Publish Video'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
