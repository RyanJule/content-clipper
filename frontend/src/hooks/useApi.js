import { useCallback, useState } from 'react'
import toast from 'react-hot-toast'

export const useApi = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const execute = useCallback(async (apiCall, options = {}) => {
    const { successMessage, errorMessage, onSuccess, onError } = options

    setLoading(true)
    setError(null)

    try {
      const result = await apiCall()

      if (successMessage) {
        toast.success(successMessage)
      }

      if (onSuccess) {
        onSuccess(result)
      }

      return result
    } catch (err) {
      const message = err.response?.data?.detail || errorMessage || 'An error occurred'
      setError(message)
      toast.error(message)

      if (onError) {
        onError(err)
      }

      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return { loading, error, execute }
}