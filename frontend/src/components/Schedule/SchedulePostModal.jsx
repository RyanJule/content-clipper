import { Calendar, Clock, Loader, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { scheduleService } from '../../services/scheduleService'
import { useStore } from '../../store'

/**
 * SchedulePostModal
 *
 * Props:
 *   onClose()           – called when user dismisses
 *   onSuccess(post)     – called with the newly-created ScheduledPost
 *   initialCaption      – pre-filled caption/title from the calling studio modal
 *   initialScheduleId   – pre-selected schedule id (e.g. from CalendarView slot click)
 *   initialScheduledFor – pre-selected ISO datetime string (e.g. from CalendarView slot)
 */
export default function SchedulePostModal({
  onClose,
  onSuccess,
  initialCaption = '',
  initialScheduleId = null,
  initialScheduledFor = null,
}) {
  const { schedules } = useStore()

  const [scheduleId, setScheduleId] = useState(initialScheduleId ?? '')
  const [caption, setCaption] = useState(initialCaption)
  const [hashtags, setHashtags] = useState('')
  const [scheduledFor, setScheduledFor] = useState(
    initialScheduledFor
      ? toLocalDatetimeInput(initialScheduledFor)
      : defaultDatetimeInput()
  )
  const [slots, setSlots] = useState([])
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Load slots whenever date or scheduleId changes
  useEffect(() => {
    const dateStr = scheduledFor?.slice(0, 10)
    if (!dateStr) return
    const [year, month, day] = dateStr.split('-').map(Number)
    setLoadingSlots(true)
    scheduleService
      .getDaySlots(year, month, day)
      .then(data => setSlots(data))
      .catch(() => setSlots([]))
      .finally(() => setLoadingSlots(false))
  }, [scheduledFor?.slice(0, 10)])

  const handleSlotPick = slot => {
    setScheduleId(slot.schedule_id)
    setScheduledFor(toLocalDatetimeInput(slot.scheduled_for))
  }

  const handleSubmit = async e => {
    e.preventDefault()
    if (!scheduleId) {
      toast.error('Please select a schedule')
      return
    }
    if (!scheduledFor) {
      toast.error('Please select a date and time')
      return
    }

    setSubmitting(true)
    try {
      const hashtagList = hashtags
        .split(/[\s,]+/)
        .map(h => h.replace(/^#/, '').trim())
        .filter(Boolean)

      const post = await scheduleService.createPost({
        schedule_id: Number(scheduleId),
        scheduled_for: new Date(scheduledFor).toISOString(),
        caption: caption.trim() || null,
        hashtags: hashtagList.length ? hashtagList : null,
        status: 'scheduled',
      })

      toast.success('Post scheduled!')
      onSuccess?.(post)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to schedule post')
    } finally {
      setSubmitting(false)
    }
  }

  const availableSlots = slots.filter(s => !s.is_taken)
  const selectedDateStr = scheduledFor?.slice(0, 10)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-5 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-primary-600" />
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
              Content Schedule <span className="text-red-500">*</span>
            </label>
            {schedules.length === 0 ? (
              <p className="text-sm text-amber-600">
                No schedules found. Create a schedule first from the Schedules page.
              </p>
            ) : (
              <select
                value={scheduleId}
                onChange={e => setScheduleId(e.target.value)}
                className="input"
                required
              >
                <option value="">Select a schedule…</option>
                {schedules.map(s => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Date & time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date &amp; Time <span className="text-red-500">*</span>
            </label>
            <input
              type="datetime-local"
              value={scheduledFor}
              onChange={e => setScheduledFor(e.target.value)}
              className="input"
              required
            />
          </div>

          {/* Available slots for the chosen date */}
          {selectedDateStr && (
            <div>
              <div className="flex items-center space-x-1 mb-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">
                  Available slots on {selectedDateStr}
                </span>
                {loadingSlots && <Loader className="w-3 h-3 animate-spin text-gray-400" />}
              </div>
              {!loadingSlots && availableSlots.length === 0 && (
                <p className="text-xs text-gray-400">
                  No open slots from active schedules for this day.
                </p>
              )}
              {availableSlots.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {availableSlots.map((slot, i) => {
                    const slotLocal = toLocalDatetimeInput(slot.scheduled_for)
                    const isActive = slotLocal === scheduledFor && String(slot.schedule_id) === String(scheduleId)
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => handleSlotPick(slot)}
                        className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                          isActive
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-primary-400'
                        }`}
                      >
                        {slot.time} · {slot.schedule_name}
                      </button>
                    )
                  })}
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
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400 resize-none"
            />
          </div>

          {/* Hashtags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Hashtags <span className="text-gray-400 font-normal">(space or comma separated)</span>
            </label>
            <input
              type="text"
              value={hashtags}
              onChange={e => setHashtags(e.target.value)}
              placeholder="#marketing #content"
              className="input"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-1">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !scheduleId || !scheduledFor}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <span className="flex items-center space-x-2">
                  <Loader className="w-4 h-4 animate-spin" />
                  <span>Scheduling…</span>
                </span>
              ) : (
                'Schedule Post'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── helpers ──────────────────────────────────────────────────────────────────

function toLocalDatetimeInput(isoOrDatetime) {
  const d = new Date(isoOrDatetime)
  if (isNaN(d)) return ''
  // datetime-local requires "YYYY-MM-DDTHH:MM"
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function defaultDatetimeInput() {
  const d = new Date()
  d.setMinutes(d.getMinutes() + 30, 0, 0)
  return toLocalDatetimeInput(d)
}
