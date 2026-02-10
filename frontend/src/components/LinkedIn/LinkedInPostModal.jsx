import { FileText, Image, Link, Upload, Video, X } from 'lucide-react'
import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { linkedinService } from '../../services/linkedinService'

const POST_TYPES = [
  { id: 'text', label: 'Text', icon: FileText },
  { id: 'image', label: 'Image', icon: Image },
  { id: 'video', label: 'Video', icon: Video },
  { id: 'article', label: 'Article', icon: Link },
]

export default function LinkedInPostModal({
  onClose,
  onSuccess,
  organizations = [],
  personUrn = '',
}) {
  const [postType, setPostType] = useState('text')
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [articleUrl, setArticleUrl] = useState('')
  const [articleTitle, setArticleTitle] = useState('')
  const [articleDescription, setArticleDescription] = useState('')
  const [altText, setAltText] = useState('')
  const [videoTitle, setVideoTitle] = useState('')
  const [visibility, setVisibility] = useState('PUBLIC')
  const [authorUrn, setAuthorUrn] = useState(personUrn)
  const [publishing, setPublishing] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef(null)

  const handleFileSelect = e => {
    const selected = e.target.files[0]
    if (!selected) return

    if (postType === 'image') {
      if (!selected.type.startsWith('image/')) {
        toast.error('Please select an image file')
        return
      }
      if (selected.size > 10 * 1024 * 1024) {
        toast.error('Image must be under 10MB')
        return
      }
    } else if (postType === 'video') {
      if (!selected.type.startsWith('video/')) {
        toast.error('Please select a video file')
        return
      }
      if (selected.size > 200 * 1024 * 1024) {
        toast.error('Video must be under 200MB')
        return
      }
    }

    setFile(selected)
    if (postType === 'video' && !videoTitle) {
      const name = selected.name.replace(/\.[^/.]+$/, '')
      setVideoTitle(name)
    }
  }

  const handlePublish = async e => {
    e.preventDefault()

    if (!text.trim() && postType !== 'article') {
      toast.error('Please enter post text')
      return
    }

    if (postType === 'image' && !file) {
      toast.error('Please select an image')
      return
    }

    if (postType === 'video' && !file) {
      toast.error('Please select a video')
      return
    }

    if (postType === 'article' && !articleUrl.trim()) {
      toast.error('Please enter an article URL')
      return
    }

    setPublishing(true)
    setUploadProgress(0)

    try {
      let result

      switch (postType) {
        case 'text':
          result = await linkedinService.createTextPost(text, authorUrn || null, visibility)
          break

        case 'image':
          result = await linkedinService.createImagePost(
            file,
            {
              text,
              alt_text: altText,
              author_urn: authorUrn || null,
              visibility,
            },
            percent => setUploadProgress(percent)
          )
          break

        case 'video':
          result = await linkedinService.createVideoPost(
            file,
            {
              text,
              title: videoTitle,
              author_urn: authorUrn || null,
              visibility,
            },
            percent => setUploadProgress(percent)
          )
          break

        case 'article':
          result = await linkedinService.createArticlePost(text, articleUrl, {
            title: articleTitle,
            description: articleDescription,
            author_urn: authorUrn || null,
            visibility,
          })
          break

        default:
          throw new Error('Unknown post type')
      }

      if (result.success) {
        onSuccess(result)
      } else {
        toast.error('Post creation failed')
      }
    } catch (error) {
      console.error('LinkedIn post failed:', error)
      toast.error(error.response?.data?.detail || 'Failed to create post')
    } finally {
      setPublishing(false)
    }
  }

  const formatFileSize = bytes => {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
    return (bytes / 1024).toFixed(1) + ' KB'
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-700 p-2 rounded-lg text-white">
              <FileText className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Create LinkedIn Post</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" disabled={publishing}>
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handlePublish} className="p-6 space-y-4">
          {/* Post Type Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Post Type</label>
            <div className="grid grid-cols-4 gap-2">
              {POST_TYPES.map(type => (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => {
                    setPostType(type.id)
                    setFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  disabled={publishing}
                  className={`flex flex-col items-center p-3 rounded-lg border-2 transition-colors ${
                    postType === type.id
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  <type.icon className="w-5 h-5 mb-1" />
                  <span className="text-xs font-medium">{type.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Author Selector (Personal vs Company) */}
          {organizations.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Post As</label>
              <select
                value={authorUrn}
                onChange={e => setAuthorUrn(e.target.value)}
                className="input"
                disabled={publishing}
              >
                <option value={personUrn}>Personal Profile</option>
                {organizations.map(org => (
                  <option key={org.id} value={org.urn}>
                    {org.name} (Company Page)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Post Text */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {postType === 'article' ? 'Commentary' : 'Post Text'}{' '}
              {postType !== 'article' && <span className="text-red-500">*</span>}
            </label>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              maxLength={3000}
              rows={5}
              placeholder={
                postType === 'article'
                  ? 'Add your thoughts about this article...'
                  : 'What do you want to talk about?'
              }
              className="input"
              disabled={publishing}
            />
            <p className="text-xs text-gray-400 mt-1">{text.length}/3000 characters</p>
          </div>

          {/* Image/Video File Upload */}
          {(postType === 'image' || postType === 'video') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {postType === 'image' ? 'Image' : 'Video'} File <span className="text-red-500">*</span>
              </label>
              <input
                type="file"
                ref={fileInputRef}
                accept={postType === 'image' ? 'image/*' : 'video/*'}
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
                    disabled={publishing}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors"
                >
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">
                    Click to select {postType === 'image' ? 'an image' : 'a video'} file
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {postType === 'image'
                      ? 'JPG, PNG, GIF, WebP (max 10MB)'
                      : 'MP4, MOV, AVI (max 200MB)'}
                  </p>
                </button>
              )}
            </div>
          )}

          {/* Image Alt Text */}
          {postType === 'image' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Alt Text <span className="text-gray-500">(optional)</span>
              </label>
              <input
                type="text"
                value={altText}
                onChange={e => setAltText(e.target.value)}
                placeholder="Describe this image for accessibility"
                className="input"
                disabled={publishing}
              />
            </div>
          )}

          {/* Video Title */}
          {postType === 'video' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Video Title <span className="text-gray-500">(optional)</span>
              </label>
              <input
                type="text"
                value={videoTitle}
                onChange={e => setVideoTitle(e.target.value)}
                placeholder="Give your video a title"
                className="input"
                disabled={publishing}
              />
            </div>
          )}

          {/* Article URL */}
          {postType === 'article' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Article URL <span className="text-red-500">*</span>
                </label>
                <input
                  type="url"
                  value={articleUrl}
                  onChange={e => setArticleUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  className="input"
                  disabled={publishing}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title Override <span className="text-gray-500">(optional)</span>
                </label>
                <input
                  type="text"
                  value={articleTitle}
                  onChange={e => setArticleTitle(e.target.value)}
                  placeholder="LinkedIn will auto-fetch the title if left empty"
                  className="input"
                  disabled={publishing}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description Override <span className="text-gray-500">(optional)</span>
                </label>
                <input
                  type="text"
                  value={articleDescription}
                  onChange={e => setArticleDescription(e.target.value)}
                  placeholder="LinkedIn will auto-fetch the description if left empty"
                  className="input"
                  disabled={publishing}
                />
              </div>
            </>
          )}

          {/* Visibility */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Visibility</label>
            <select
              value={visibility}
              onChange={e => setVisibility(e.target.value)}
              className="input"
              disabled={publishing}
            >
              <option value="PUBLIC">Public</option>
              <option value="CONNECTIONS">Connections Only</option>
              <option value="LOGGED_IN">LinkedIn Members Only</option>
            </select>
          </div>

          {/* Upload Progress */}
          {publishing && (postType === 'image' || postType === 'video') && (
            <div>
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>{postType === 'video' ? 'Uploading video...' : 'Uploading image...'}</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              {postType === 'video' && uploadProgress === 100 && (
                <p className="text-xs text-gray-500 mt-1">Processing video on LinkedIn...</p>
              )}
            </div>
          )}

          {publishing && postType === 'text' && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span>Publishing post...</span>
            </div>
          )}

          {publishing && postType === 'article' && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span>Sharing article...</span>
            </div>
          )}

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
              className="btn btn-primary bg-blue-700 hover:bg-blue-800"
              disabled={
                publishing ||
                (!text.trim() && postType !== 'article') ||
                ((postType === 'image' || postType === 'video') && !file) ||
                (postType === 'article' && !articleUrl.trim())
              }
            >
              {publishing ? 'Publishing...' : 'Publish to LinkedIn'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
