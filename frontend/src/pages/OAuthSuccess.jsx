// frontend/src/pages/OAuthSuccess.jsx
import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'

export default function OAuthSuccess() {
  const [searchParams] = useSearchParams()
  const platform = searchParams.get('platform')
  const error = searchParams.get('error')

  useEffect(() => {
    if (window.opener) {
      if (error) {
        window.opener.postMessage(
          { type: 'OAUTH_ERROR', error },
          window.location.origin
        )
      } else {
        window.opener.postMessage(
          { type: 'OAUTH_SUCCESS', platform },
          window.location.origin
        )
      }
      // Give the parent window time to process the message before closing
      setTimeout(() => window.close(), 500)
    }
  }, [platform, error])

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
      {error ? (
        <>
          <div className="text-red-500 text-4xl mb-4">&#10007;</div>
          <h2 className="text-xl font-semibold text-red-600">Connection Failed</h2>
          <p className="text-gray-600 mt-2">{error}</p>
          <p className="text-gray-400 mt-4 text-sm">You can close this window.</p>
        </>
      ) : (
        <>
          <div className="text-green-500 text-4xl mb-4">&#10003;</div>
          <h2 className="text-xl font-semibold text-green-600">Account Connected!</h2>
          <p className="text-gray-600 mt-2">
            Your {platform} account has been connected successfully.
          </p>
          <p className="text-gray-400 mt-4 text-sm">This window will close automatically...</p>
        </>
      )}
    </div>
  )
}
