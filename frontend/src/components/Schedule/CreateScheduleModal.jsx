import { Lightbulb, TrendingUp, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { scheduleService } from '../../services/scheduleService'

const daysOfWeek = [
  { id: 0, name: 'Monday', short: 'Mon' },
  { id: 1, name: 'Tuesday', short: 'Tue' },
  { id: 2, name: 'Wednesday', short: 'Wed' },
  { id: 3, name: 'Thursday', short: 'Thu' },
  { id: 4, name: 'Friday', short: 'Fri' },
  { id: 5, name: 'Saturday', short: 'Sat' },
  { id: 6, name: 'Sunday', short: 'Sun' },
]

export default function CreateScheduleModal({ schedule, accounts, onClose, onSuccess }) {
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    account_id: '',
    days_of_week: [],
    posting_times: ['09:00'],
    timezone: 'UTC',
    is_active: true,
  })
  const [suggestions, setSuggestions] = useState([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (schedule) {
      setFormData({
        name: schedule.name,
        description: schedule.description || '',
        account_id: schedule.account_id,
        days_of_week: schedule.days_of_week,
        posting_times: schedule.posting_times,
        timezone: schedule.timezone,
        is_active: schedule.is_active,
      })
    }
  }, [schedule])

  const loadSuggestions = async platform => {
    setLoadingSuggestions(true)
    try {
      const data = await scheduleService.getSuggestions(platform)
      setSuggestions(data)
    } catch (error) {
      console.error('Failed to load suggestions:', error)
    } finally {
      setLoadingSuggestions(false)
    }
  }

  const handleAccountChange = accountId => {
    setFormData({ ...formData, account_id: accountId })
    const account = accounts.find(a => a.id === parseInt(accountId))
    if (account) {
      loadSuggestions(account.platform)
    }
  }

  const applySuggestion = suggestion => {
    setFormData({
      ...formData,
      name: suggestion.name,
      description: suggestion.description,
      days_of_week: suggestion.days_of_week,
      posting_times: suggestion.posting_times,
    })
    setStep(2)
  }

  const toggleDay = dayId => {
    if (formData.days_of_week.includes(dayId)) {
      setFormData({
        ...formData,
        days_of_week: formData.days_of_week.filter(d => d !== dayId),
      })
    } else {
      setFormData({
        ...formData,
        days_of_week: [...formData.days_of_week, dayId].sort((a, b) => a - b),
      })
    }
  }

  const addPostingTime = () => {
    setFormData({
      ...formData,
      posting_times: [...formData.posting_times, '12:00'],
    })
  }

  const updatePostingTime = (index, value) => {
    const newTimes = [...formData.posting_times]
    newTimes[index] = value
    setFormData({ ...formData, posting_times: newTimes })
  }

  const removePostingTime = index => {
    setFormData({
      ...formData,
      posting_times: formData.posting_times.filter((_, i) => i !== index),
    })
  }

  const handleSubmit = async e => {
    e.preventDefault()

    if (formData.days_of_week.length === 0) {
      toast.error('Please select at least one day')
      return
    }

    if (formData.posting_times.length === 0) {
      toast.error('Please add at least one posting time')
      return
    }

    setLoading(true)

    try {
      if (schedule) {
        await scheduleService.updateSchedule(schedule.id, formData)
        toast.success('Schedule updated successfully!')
      } else {
        await scheduleService.createSchedule(formData)
        toast.success('Schedule created successfully!')
      }
      onSuccess()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save schedule')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <h2 className="text-2xl font-bold text-gray-900">
            {schedule ? 'Edit Schedule' : 'Create Schedule'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Step 1: Choose Account & View Suggestions */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Account *
                </label>
                <select
                  value={formData.account_id}
                  onChange={e => handleAccountChange(e.target.value)}
                  className="input"
                  required
                >
                  <option value="">Choose an account...</option>
                  {accounts.map(account => (
                    <option key={account.id} value={account.id}>
                      {account.platform} - @{account.account_username}
                    </option>
                  ))}
                </select>
              </div>

              {formData.account_id && (
                <>
                  <div className="border-t border-gray-200 pt-6">
                    <div className="flex items-center space-x-2 mb-4">
                      <Lightbulb className="w-5 h-5 text-yellow-500" />
                      <h3 className="text-lg font-semibold text-gray-900">
                        Suggested Schedules
                      </h3>
                    </div>

                    {loadingSuggestions ? (
                      <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                        <p className="text-gray-600 mt-2">Loading suggestions...</p>
                      </div>
                    ) : suggestions.length > 0 ? (
                      <div className="space-y-3">
                        {suggestions.map((suggestion, index) => (
                          <div
                            key={index}
                            className="card p-4 hover:shadow-md transition-shadow cursor-pointer"
                            onClick={() => applySuggestion(suggestion)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-900">{suggestion.name}</h4>
                                <p className="text-sm text-gray-600 mt-1">
                                  {suggestion.description}
                                </p>
                                <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                                  <span>
                                    {suggestion.days_of_week.length} days/week
                                  </span>
                                  <span>
                                    {suggestion.posting_times.length} posts/day
                                  </span>
                                </div>
                                <div className="mt-2 flex items-center space-x-4 text-sm">
                                  <span className="flex items-center space-x-1">
                                    <TrendingUp className="w-4 h-4 text-green-600" />
                                    <span className="text-green-600">
                                      {suggestion.estimated_engagement}% engagement
                                    </span>
                                  </span>
                                  <span className="text-gray-600">
                                    {suggestion.estimated_growth}% growth
                                  </span>
                                </div>
                              </div>
                              <button className="btn btn-primary text-sm">
                                Use This
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-600">No suggestions available</p>
                    )}
                  </div>

                  <div className="flex justify-between pt-4">
                    <button
                      type="button"
                      onClick={() => setStep(2)}
                      className="btn btn-secondary"
                    >
                      Skip Suggestions
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Step 2: Custom Schedule */}
          {step === 2 && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Schedule Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  className="input"
                  placeholder="e.g., Weekday Posting Schedule"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                  className="input"
                  rows="2"
                  placeholder="Optional description"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Posting Days *
                </label>
                <div className="flex flex-wrap gap-2">
                  {daysOfWeek.map(day => (
                    <button
                      key={day.id}
                      type="button"
                      onClick={() => toggleDay(day.id)}
                      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        formData.days_of_week.includes(day.id)
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {day.short}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Posting Times *
                </label>
                <div className="space-y-2">
                  {formData.posting_times.map((time, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <input
                        type="time"
                        value={time}
                        onChange={e => updatePostingTime(index, e.target.value)}
                        className="input flex-1"
                        required
                      />
                      {formData.posting_times.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removePostingTime(index)}
                          className="btn btn-danger text-sm"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={addPostingTime}
                  className="mt-2 text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  + Add Another Time
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
                <select
                  value={formData.timezone}
                  onChange={e => setFormData({ ...formData, timezone: e.target.value })}
                  className="input"
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                  Activate this schedule immediately
                </label>
              </div>

              <div className="flex justify-between pt-4">
                {!schedule && (
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="btn btn-secondary"
                  >
                    Back
                  </button>
                )}
                <div className="flex-1" />
                <button type="submit" disabled={loading} className="btn btn-primary">
                  {loading ? 'Saving...' : schedule ? 'Update Schedule' : 'Create Schedule'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}