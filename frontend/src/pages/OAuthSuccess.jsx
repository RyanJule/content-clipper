// frontend/src/pages/OAuthSuccess.jsx
import { useEffect } from 'react'

export default function OAuthSuccess() {
  useEffect(() => {
    // Send message to parent window
    if (window.opener) {
      window.opener.postMessage({ type: 'OAUTH_SUCCESS' }, window.origin)
      window.close() // close popup
    }
  }, [])

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h2 className="text-xl font-semibold">Connecting your account...</h2>
      <p className="text-gray-600 mt-2">Please wait, this window will close automatically.</p>
    </div>
  )
}
