/**
 * SchedulePostModal – schedule a post for a specific date/time.
 *
 * Can be used from any studio upload modal after media has been uploaded,
 * or standalone from the calendar to create a new slot.
 *
 * Props:
 *   onClose()          – close without saving
 *   onSuccess(post)    – called with the created ScheduledPost
 *   initialCaption     – pre-filled caption (from parent modal)
 *   initialHashtags    – pre-filled hashtags array
 *   initialDate        – pre-selected date (Date object or ISO string)
 *   initialScheduleId  – pre-selected ContentSchedule id
 *   initialSlotTime    – pre-selected time (HH:MM) from a schedule slot
 *   accounts           – list of connected accounts (passed in so we don't re-fetch)
 *   schedules          – list of ContentSchedules (passed in so we don't re-fetch)
 */

import { Calendar, Clock, Hash, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { scheduleService } from '../../services/scheduleService'
import { useStore } from '../../store'

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function formatDateForInput(d) {
  if (!d) return ''
  const date = d instanceof Date ? d : new Date(d)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatTimeForInput(d) {
  if (!d) return ''
  const date = d instanceof Date ? d : new Date(d)
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${h}:${min}`
}

export default function SchedulePostModal({
  onClose,
  onSuccess,
  initialCaption = '',
  initialHashtags = [],
  initialDate = null,
  initialScheduleId = null,
  initialSlotTime = null,
  accounts: accountsProp = null,
  schedules: schedulesProp = null,
}) {
  const { accounts: storeAccounts, schedules: storeSchedules } = useStore()

  const accounts = accountsProp ?? storeAccounts
  const schedules = schedulesProp ?? storeSchedules

  // Form state
  const [scheduleId, setScheduleId] = useState(initialScheduleId ?? '')
  const [date, setDate] = useState(formatDateForInput(initialDate) || formatDateForInput(new Date()))
  const [time, setTime] = useState(
    initialSlotTime || (initialDate ? formatTimeForInput(initialDate) : '09:00')
  )
  const [caption, setCaption] = useState(initialCaption)
  const [hashtagInput, setHashtagInput] = useState(
    Array.isArray(initialHashtags) ? initialHashtags.join(' ') : ''
  )

  // Slot suggestions from selected schedule + date
  const [slots, setSlots] = useState([])
  const [loadingSlots, setLoadingSlots] = useState(false)

  const [saving, setSaving] = useState(false)

  // When schedule or date changes, load available slots
  useEffect(() => {
    if (!scheduleId || !date) {
      setSlots([])
      return
    }
    const [y, m, d] = date.split('-').map(Number)
    if (!y || !m || !d) return

    const selectedSchedule = schedules.find(s => s.id === Number(scheduleId))
    if (!selectedSchedule) return

    setLoadingSlots(true)
    scheduleService
      .getDaySlots(y, m, d, selectedSchedule.account_id)
      .then(data => {
        // Filter slots from this schedule only
        setSlots(data.filter(s => s.schedule_id === Number(scheduleId)))
      })
      .catch(() => setSlots([]))
      .finally(() => setLoadingSlots(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scheduleId, date])

  const selectedSchedule = schedules.find(s => s.id === Number(scheduleId))

  const handleSubmit = async e => {
    e.preventDefault()

    if (!scheduleId) {
      toast.error('Please select a schedule')
      return
    }
    if (!date || !time) {
      toast.error('Please select a date and time')
      return
    }

    const scheduledFor = new Date(`${date}T${time}:00`)
    if (isNaN(scheduledFor.getTime())) {
      toast.error('Invalid date/time')
      return
    }

    const hashtags = hashtagInput
      .split(/[\s,]+/)
      .map(h => h.replace(/^#/, '').trim())
      .filter(Boolean)

    setSaving(true)
    try {
      const post = await scheduleService.createPost({
        schedule_id: Number(scheduleId),
        scheduled_for: scheduledFor.toISOString(),
        caption: caption.trim() || null,
        hashtags: hashtags.length > 0 ? hashtags : null,
        status: 'scheduled',
      })
      toast.success('Post scheduled!')
      onSuccess?.(post)
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to schedule post'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-5 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-2">
            <div className="bg-blue-100 p-1.5 rounded-lg">
              <Calendar className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="text-lg font-bold text-gray-900">Schedule Post</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {/* Schedule selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Posting Schedule <span className="text-red-500">*</span>
            </label>
            {schedules.length === 0 ? (
              <p className="text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-3">
                No schedules found. Go to{' '}
                <a href="/schedules" className="underline font-medium">
                  Schedules
                </a>{' '}
                to create one first.
              </p>
            ) : (
              <select
                value={scheduleId}
                onChange={e => setScheduleId(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                required
              >
                <option value="">Select a schedule…</option>
                {schedules.map(s => {
                  const account = accounts.find(a => a.id === s.account_id)
                  const label = account
                    ? `${s.name} (${account.platform} @${account.account_username})`
                    : s.name
                  return (
                    <option key={s.id} value={s.id}>
                      {label}
                    </option>
                  )
                })}
              </select>
            )}

            {selectedSchedule && (
              <div className="mt-2 flex flex-wrap gap-1">
                {selectedSchedule.days_of_week.map(d => (
                  <span
                    key={d}
                    className="text-xs bg-blue-50 text-blue-700 rounded px-1.5 py-0.5 font-medium"
                  >
                    {DAY_NAMES[d]}
                  </span>
                ))}
                <span className="text-xs text-gray-400 ml-1">
                  at {selectedSchedule.posting_times.join(', ')}
                </span>
              </div>
            )}
          </div>

          {/* Date + Time */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" /> Date
                </span>
              </label>
              <input
                type="date"
                value={date}
                onChange={e => setDate(e.target.value)}
                min={formatDateForInput(new Date())}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" /> Time
                </span>
              </label>
              <input
                type="time"
                value={time}
                onChange={e => setTime(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                required
              />
            </div>
          </div>

          {/* Slot quick-pick */}
          {scheduleId && date && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Schedule Slots for This Day
              </label>
              {loadingSlots ? (
                <p className="text-xs text-gray-400">Loading slots…</p>
              ) : slots.length === 0 ? (
                <p className="text-xs text-gray-400">
                  No slots defined for this day in the selected schedule.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {slots.map(slot => (
                    <button
                      key={slot.slot_time}
                      type="button"
                      onClick={() => setTime(slot.slot_time)}
                      disabled={slot.is_taken}
                      className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                        time === slot.slot_time
                          ? 'border-blue-500 bg-blue-500 text-white'
                          : slot.is_taken
                          ? 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed line-through'
                          : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50 text-gray-700'
                      }`}
                    >
                      {slot.slot_time}
                      {slot.is_taken && ' (taken)'}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Caption */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Caption</label>
            <textarea
              value={caption}
              onChange={e => setCaption(e.target.value)}
              rows={3}
              placeholder="Write a caption…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
            />
          </div>

          {/* Hashtags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <span className="flex items-center gap-1">
                <Hash className="w-3.5 h-3.5" /> Hashtags
              </span>
            </label>
            <input
              type="text"
              value={hashtagInput}
              onChange={e => setHashtagInput(e.target.value)}
              placeholder="#content #social (space or comma separated)"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            <p className="text-xs text-gray-400 mt-1">
              The # prefix is optional — it will be added automatically.
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-1">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !scheduleId}
              className="btn btn-primary bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Scheduling…' : 'Schedule Post'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
