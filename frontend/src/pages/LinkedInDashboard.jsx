import {
  Building2,
  ExternalLink,
  FileText,
  Image,
  Link,
  Linkedin,
  Plus,
  Trash2,
  Video,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useApi } from '../hooks/useApi'
import { linkedinService } from '../services/linkedinService'
import LinkedInPostModal from '../components/LinkedIn/LinkedInPostModal'

export default function LinkedInDashboard() {
  const { loading, execute } = useApi()
  const [profile, setProfile] = useState(null)
  const [organizations, setOrganizations] = useState([])
  const [posts, setPosts] = useState([])
  const [showPostModal, setShowPostModal] = useState(false)

  useEffect(() => {
    loadProfile()
    loadOrganizations()
  }, [])

  const loadProfile = () => {
    execute(
      async () => {
        const data = await linkedinService.getProfile()
        setProfile(data)
        // Load posts after profile is available
        if (data.person_urn) {
          const postsData = await linkedinService.getPosts(data.person_urn, 20)
          setPosts(postsData.posts || [])
        }
      },
      { errorMessage: 'Failed to load LinkedIn profile. Please connect your account first.' }
    )
  }

  const loadOrganizations = () => {
    execute(
      async () => {
        const data = await linkedinService.getOrganizations()
        setOrganizations(data.organizations || [])
      },
      { errorMessage: null } // Silently fail - orgs are optional
    )
  }

  const loadPosts = () => {
    if (!profile?.person_urn) return
    execute(
      async () => {
        const data = await linkedinService.getPosts(profile.person_urn, 20)
        setPosts(data.posts || [])
      },
      { errorMessage: 'Failed to load posts' }
    )
  }

  const handleDeletePost = async postUrn => {
    if (!window.confirm('Are you sure you want to delete this post? This cannot be undone.')) return

    execute(
      async () => {
        await linkedinService.deletePost(postUrn)
        setPosts(prev => prev.filter(p => (p.id || p.urn) !== postUrn))
      },
      {
        successMessage: 'Post deleted successfully',
        errorMessage: 'Failed to delete post',
      }
    )
  }

  const handlePostSuccess = result => {
    setShowPostModal(false)
    toast.success('Post published to LinkedIn!')
    loadPosts()
  }

  const getPostTypeIcon = post => {
    const content = post.content || {}
    if (content.media) {
      const mediaType = content.media.id || ''
      if (mediaType.includes('video')) return <Video className="w-4 h-4 text-purple-600" />
      if (mediaType.includes('image')) return <Image className="w-4 h-4 text-green-600" />
    }
    if (content.article) return <Link className="w-4 h-4 text-orange-600" />
    return <FileText className="w-4 h-4 text-blue-600" />
  }

  if (loading && !profile && posts.length === 0) {
    return (
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">LinkedIn</h2>
        <p className="text-gray-600 mb-6">Manage your LinkedIn profile and posts</p>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading LinkedIn...</p>
        </div>
      </div>
    )
  }

  if (!profile && !loading) {
    return (
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">LinkedIn</h2>
        <p className="text-gray-600 mb-6">Manage your LinkedIn profile and posts</p>
        <div className="card p-12 text-center">
          <Linkedin className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No LinkedIn Account Connected</h3>
          <p className="text-gray-600 mb-6">
            Connect your LinkedIn account from the Accounts page to get started.
          </p>
          <a href="/accounts" className="btn btn-primary inline-flex items-center space-x-2">
            <Plus className="w-5 h-5" />
            <span>Connect LinkedIn</span>
          </a>
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">LinkedIn</h2>
          <p className="text-gray-600 mt-1">Manage your LinkedIn profile and posts</p>
        </div>
        <button
          onClick={() => setShowPostModal(true)}
          className="btn btn-primary bg-blue-700 hover:bg-blue-800 flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Create Post</span>
        </button>
      </div>

      {/* Profile Card + Organizations */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Profile Info */}
        {profile && (
          <div className="card p-4 md:col-span-2">
            <div className="flex items-center space-x-4">
              {profile.picture ? (
                <img
                  src={profile.picture}
                  alt={profile.name}
                  className="w-14 h-14 rounded-full"
                />
              ) : (
                <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center">
                  <Linkedin className="w-7 h-7 text-blue-700" />
                </div>
              )}
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{profile.name}</h3>
                <p className="text-sm text-gray-500">{profile.email}</p>
                <p className="text-xs text-gray-400 mt-1 font-mono">{profile.person_urn}</p>
              </div>
            </div>
          </div>
        )}

        {/* Organizations */}
        <div className="card p-4">
          <div className="flex items-center space-x-2 mb-3">
            <Building2 className="w-5 h-5 text-gray-600" />
            <h4 className="font-semibold text-gray-900">Company Pages</h4>
          </div>
          {organizations.length > 0 ? (
            <ul className="space-y-2">
              {organizations.map(org => (
                <li key={org.id} className="text-sm text-gray-700 flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  <span>{org.name}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No company pages found</p>
          )}
        </div>
      </div>

      {/* Posts List */}
      <div className="card">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Recent Posts</h3>
          <button onClick={loadPosts} className="text-sm text-blue-600 hover:text-blue-700" disabled={loading}>
            Refresh
          </button>
        </div>

        {posts.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No posts yet</p>
            <p className="text-sm text-gray-400 mt-1">Create your first LinkedIn post to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {posts.map((post, index) => {
              const postUrn = post.id || post.urn || `post-${index}`
              const commentary = post.commentary || ''
              const createdAt = post.createdAt
                ? new Date(post.createdAt).toLocaleDateString()
                : post.lastModifiedAt
                  ? new Date(post.lastModifiedAt).toLocaleDateString()
                  : ''
              const postVisibility = post.visibility || 'PUBLIC'

              return (
                <div key={postUrn} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start space-x-3">
                    {/* Post Type Icon */}
                    <div className="mt-1 flex-shrink-0">{getPostTypeIcon(post)}</div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 line-clamp-3">
                        {commentary || '(No text content)'}
                      </p>

                      {/* Article link if present */}
                      {post.content?.article?.source && (
                        <a
                          href={post.content.article.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:underline mt-1 block truncate"
                        >
                          {post.content.article.source}
                        </a>
                      )}

                      <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
                        <span
                          className={`px-2 py-0.5 rounded ${
                            postVisibility === 'PUBLIC'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {postVisibility}
                        </span>
                        {createdAt && <span>{createdAt}</span>}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      {post.content?.article?.source && (
                        <a
                          href={post.content.article.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-secondary text-sm p-2"
                          title="Open article"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                      <button
                        onClick={() => handleDeletePost(postUrn)}
                        className="btn btn-danger text-sm p-2"
                        title="Delete post"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Post Modal */}
      {showPostModal && (
        <LinkedInPostModal
          onClose={() => setShowPostModal(false)}
          onSuccess={handlePostSuccess}
          organizations={organizations}
          personUrn={profile?.person_urn || ''}
        />
      )}
    </div>
  )
}
