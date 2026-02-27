import { CheckCircle, Film, Image, LayoutGrid, Loader, Plus, Upload, Video, X } from 'lucide-react'
import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { instagramService } from '../../services/instagramService'
import { mediaService } from '../../services/mediaService'

const TABS = [
  { id: 'image', label: 'Single Image', icon: Image, accept: 'image/jpeg,.jpg,.jpeg' },
  { id: 'carousel', label: 'Carousel', icon: LayoutGrid, accept: 'image/jpeg,.jpg,.jpeg' },
  { id: 'video', label: 'Video', icon: Video, accept: 'video/*' },
  { id: 'reel', label: 'Reel', icon: Film, accept: 'video/*' },
]

const MAX_CAPTION = 2200
const MAX_CAROUSEL_ITEMS = 10

// ── Single-file upload zone ───────────────────────────────────────────────────

function FileDropZone({ accept, onSelect, label, hint }) {
  const ref = useRef(null)
  return (
    <button
      type="button"
      onClick={() => ref.current?.click()}
      className="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-pink-400 transition-colors"
    >
      <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-xs text-gray-400 mt-1">{hint}</p>
      <input type="file" ref={ref} accept={accept} className="hidden" onChange={onSelect} />
    </button>
  )
}

// ── File preview row ──────────────────────────────────────────────────────────

function FileRow({ file, previewUrl, onRemove, disabled }) {
  const formatSize = bytes => {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
    return (bytes / 1024).toFixed(1) + ' KB'
  }

  return (
    <div className="border border-gray-200 rounded-lg p-3 flex items-center space-x-3">
      {previewUrl && (
        <img
          src={previewUrl}
          alt=""
          className="w-12 h-12 object-cover rounded flex-shrink-0"
        />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
        <p className="text-xs text-gray-500">{formatSize(file.size)}</p>
      </div>
      {!disabled && (
        <button
          type="button"
          onClick={onRemove}
          className="text-gray-400 hover:text-red-500 flex-shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

// ── Main modal ────────────────────────────────────────────────────────────────

export default function InstagramUploadModal({ onClose, onSuccess }) {
  const [activeTab, setActiveTab] = useState('image')
  const [caption, setCaption] = useState('')

  // Single-file state (image / video / reel)
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)

  // Carousel state: array of { file, previewUrl }
  const [carouselItems, setCarouselItems] = useState([])
  const carouselInputRef = useRef(null)

  // Upload / publish lifecycle
  // 'idle' | 'uploading' | 'publishing' | 'done'
  const [stage, setStage] = useState('idle')
  const [uploadProgress, setUploadProgress] = useState(0)

  const busy = stage === 'uploading' || stage === 'publishing'

  // ── Tab switch ──────────────────────────────────────────────────────────────

  const switchTab = tab => {
    if (busy) return
    setActiveTab(tab)
    clearFile()
  }

  // ── File helpers ────────────────────────────────────────────────────────────

  const clearFile = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(null)
    setPreviewUrl(null)
    setCarouselItems(prev => {
      prev.forEach(i => URL.revokeObjectURL(i.previewUrl))
      return []
    })
    setStage('idle')
    setUploadProgress(0)
  }

  const isJpeg = f => f.type === 'image/jpeg' || /\.(jpg|jpeg)$/i.test(f.name)

  const handleSingleFileSelect = e => {
    const selected = e.target.files?.[0]
    if (!selected) return
    if (activeTab === 'image' && !isJpeg(selected)) {
      toast.error('Instagram only accepts JPEG images. Please convert your file to .jpg/.jpeg first.')
      e.target.value = ''
      return
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    const url = selected.type.startsWith('image/') ? URL.createObjectURL(selected) : null
    setFile(selected)
    setPreviewUrl(url)
  }

  const handleCarouselAdd = e => {
    const newFiles = Array.from(e.target.files || [])
    if (!newFiles.length) return
    const nonJpeg = newFiles.filter(f => !isJpeg(f))
    if (nonJpeg.length > 0) {
      toast.error('Instagram only accepts JPEG images. Please convert all files to .jpg/.jpeg first.')
      e.target.value = ''
      return
    }
    const remaining = MAX_CAROUSEL_ITEMS - carouselItems.length
    if (remaining <= 0) {
      toast.error(`Carousel supports up to ${MAX_CAROUSEL_ITEMS} images`)
      return
    }
    const toAdd = newFiles.slice(0, remaining)
    const newItems = toAdd.map(f => ({ file: f, previewUrl: URL.createObjectURL(f) }))
    setCarouselItems(prev => [...prev, ...newItems])
    // Reset input so the same files can be added again if needed
    if (carouselInputRef.current) carouselInputRef.current.value = ''
  }

  const removeCarouselItem = idx => {
    setCarouselItems(prev => {
      URL.revokeObjectURL(prev[idx].previewUrl)
      return prev.filter((_, i) => i !== idx)
    })
  }

  // ── Upload & publish ────────────────────────────────────────────────────────

  const handlePublish = async e => {
    e.preventDefault()

    if (activeTab === 'carousel') {
      if (carouselItems.length < 2) {
        toast.error('Add at least 2 images for a carousel')
        return
      }
    } else {
      if (!file) {
        toast.error('Please select a file')
        return
      }
    }

    try {
      if (activeTab === 'carousel') {
        await publishCarousel()
      } else {
        await publishSingle()
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Something went wrong'
      toast.error(msg)
      setStage('idle')
    }
  }

  const publishSingle = async () => {
    // 1. Upload to media library
    setStage('uploading')
    setUploadProgress(0)
    const uploaded = await mediaService.upload(file, pct => setUploadProgress(pct))
    const mediaId = uploaded.media_id

    // 2. Publish to Instagram
    setStage('publishing')
    if (activeTab === 'image') {
      await instagramService.publishImage(mediaId, caption.trim() || null)
    } else if (activeTab === 'video') {
      await instagramService.publishVideo(mediaId, caption.trim() || null)
    } else if (activeTab === 'reel') {
      await instagramService.publishReel(mediaId, caption.trim() || null)
    }

    setStage('done')
    toast.success('Published to Instagram!')
    onSuccess?.()
  }

  const publishCarousel = async () => {
    // 1. Upload all carousel images
    setStage('uploading')
    const mediaIds = []
    for (let i = 0; i < carouselItems.length; i++) {
      setUploadProgress(Math.round((i / carouselItems.length) * 100))
      const uploaded = await mediaService.upload(carouselItems[i].file)
      mediaIds.push(uploaded.media_id)
    }
    setUploadProgress(100)

    // 2. Publish carousel to Instagram
    setStage('publishing')
    await instagramService.publishCarousel(mediaIds, caption.trim() || null)

    setStage('done')
    toast.success('Carousel published to Instagram!')
    onSuccess?.()
  }

  // ── Derived helpers ─────────────────────────────────────────────────────────

  const currentTab = TABS.find(t => t.id === activeTab)

  const canPublish =
    !busy &&
    (activeTab === 'carousel' ? carouselItems.length >= 2 : file !== null)

  // ── Done screen ─────────────────────────────────────────────────────────────

  if (stage === 'done') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg w-full max-w-md p-8 text-center space-y-4">
          <CheckCircle className="w-14 h-14 text-green-500 mx-auto" />
          <h2 className="text-xl font-bold text-gray-900">Published!</h2>
          <p className="text-sm text-gray-600">
            Your content has been published to Instagram. It may take a moment to appear on your
            profile.
          </p>
          <button onClick={onClose} className="btn btn-primary bg-pink-600 hover:bg-pink-700">
            Done
          </button>
        </div>
      </div>
    )
  }

  // ── Upload / publish progress screen ────────────────────────────────────────

  if (busy) {
    const isUploading = stage === 'uploading'
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg w-full max-w-md p-8 text-center space-y-5">
          <Loader className="w-10 h-10 text-pink-500 animate-spin mx-auto" />
          <h2 className="text-xl font-bold text-gray-900">
            {isUploading ? 'Uploading…' : 'Publishing to Instagram…'}
          </h2>
          {isUploading && (
            <>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-pink-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-500">{uploadProgress}%</p>
            </>
          )}
          {!isUploading && (
            <p className="text-sm text-gray-500">
              {activeTab === 'video' || activeTab === 'reel'
                ? 'This may take a few minutes while Instagram processes the video.'
                : 'Almost there…'}
            </p>
          )}
        </div>
      </div>
    )
  }

  // ── Main form ───────────────────────────────────────────────────────────────

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-5 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-2">
            <div className="bg-gradient-to-br from-pink-500 to-purple-600 p-1.5 rounded-lg">
              <Upload className="w-4 h-4 text-white" />
            </div>
            <h2 className="text-lg font-bold text-gray-900">New Instagram Post</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 px-5 pt-4 space-x-1">
          {TABS.map(tab => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => switchTab(tab.id)}
                className={`flex items-center space-x-1.5 px-3 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
                  active
                    ? 'border-pink-500 text-pink-600 bg-pink-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            )
          })}
        </div>

        <form onSubmit={handlePublish} className="p-5 space-y-5">
          {/* ── Carousel tab ── */}
          {activeTab === 'carousel' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">
                  Images{' '}
                  <span className="text-gray-400 font-normal">
                    ({carouselItems.length}/{MAX_CAROUSEL_ITEMS})
                  </span>
                </label>
                {carouselItems.length < MAX_CAROUSEL_ITEMS && (
                  <button
                    type="button"
                    onClick={() => carouselInputRef.current?.click()}
                    className="flex items-center space-x-1 text-sm text-pink-600 hover:text-pink-700"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add images</span>
                  </button>
                )}
                <input
                  ref={carouselInputRef}
                  type="file"
                  accept="image/jpeg,.jpg,.jpeg"
                  multiple
                  className="hidden"
                  onChange={handleCarouselAdd}
                />
              </div>

              {carouselItems.length === 0 ? (
                <FileDropZone
                  accept="image/jpeg,.jpg,.jpeg"
                  onSelect={handleCarouselAdd}
                  label="Click to select images (2–10)"
                  hint="JPEG only (.jpg / .jpeg) — Instagram requirement"
                />
              ) : (
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {carouselItems.map((item, idx) => (
                    <div key={idx} className="flex items-center space-x-3">
                      <span className="text-xs text-gray-400 w-5 text-center flex-shrink-0">
                        {idx + 1}
                      </span>
                      <div className="flex-1">
                        <FileRow
                          file={item.file}
                          previewUrl={item.previewUrl}
                          onRemove={() => removeCarouselItem(idx)}
                          disabled={false}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {carouselItems.length > 0 && carouselItems.length < 2 && (
                <p className="text-xs text-amber-600">Add at least one more image to publish a carousel.</p>
              )}
            </div>
          )}

          {/* ── Single file tabs (image / video / reel) ── */}
          {activeTab !== 'carousel' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {activeTab === 'image' ? 'Image' : 'Video'}
              </label>
              {file ? (
                <div className="space-y-3">
                  <FileRow
                    file={file}
                    previewUrl={previewUrl}
                    onRemove={clearFile}
                    disabled={false}
                  />
                  {previewUrl && (
                    <img
                      src={previewUrl}
                      alt="Preview"
                      className="w-full max-h-48 object-contain rounded-lg bg-gray-100"
                    />
                  )}
                  {!previewUrl && file && (
                    <video
                      src={URL.createObjectURL(file)}
                      controls
                      className="w-full max-h-48 rounded-lg bg-black"
                    />
                  )}
                </div>
              ) : (
                <FileDropZone
                  accept={currentTab.accept}
                  onSelect={handleSingleFileSelect}
                  label={`Click to select ${activeTab === 'image' ? 'an image' : 'a video'}`}
                  hint={
                    activeTab === 'image'
                      ? 'JPEG only (.jpg / .jpeg) — Instagram requirement'
                      : activeTab === 'reel'
                        ? 'MP4, MOV — vertical format recommended'
                        : 'MP4, MOV supported'
                  }
                />
              )}
            </div>
          )}

          {/* Caption */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-gray-700">Caption</label>
              <span className="text-xs text-gray-400">
                {caption.length}/{MAX_CAPTION}
              </span>
            </div>
            <textarea
              value={caption}
              onChange={e => setCaption(e.target.value.slice(0, MAX_CAPTION))}
              rows={4}
              placeholder="Write a caption…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-400 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-1">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canPublish}
              className="btn btn-primary bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Publish
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
