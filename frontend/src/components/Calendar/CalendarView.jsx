import { AlertCircle, CheckCircle, ChevronLeft, ChevronRight, Clock, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { scheduleService } from '../../services/scheduleService'
import { useStore } from '../../store'
import SchedulePostModal from '../Schedule/SchedulePostModal'

export default function CalendarView({ compact = false, currentMonth: initialMonth }) {
  const {
    selectedAccountId,
    selectedBrandId,
    calendarData,
    setCalendarData,
    schedules,
    accounts,
    removeScheduledPost,
  } = useStore()

  const [currentDate, setCurrentDate] = useState(initialMonth || new Date())
  const [loading, setLoading] = useState(false)
  const [selectedDay, setSelectedDay] = useState(null)

  // Slots for the selected day (from ContentSchedule patterns)
  const [daySlots, setDaySlots] = useState([])
  const [loadingSlots, setLoadingSlots] = useState(false)

  // Schedule-post modal config; null = hidden, object = shown with pre-fill
  const [scheduleModalConfig, setScheduleModalConfig] = useState(null)

  useEffect(() => {
    loadCalendarData()
  }, [currentDate, selectedAccountId, selectedBrandId])

  // When a day is selected, load its schedule slots
  useEffect(() => {
    if (!selectedDay || compact) {
      setDaySlots([])
      return
    }
    const [y, m, d] = selectedDay.date.split('-').map(Number)
    setLoadingSlots(true)
    scheduleService
      .getDaySlots(y, m, d, selectedAccountId, selectedAccountId ? null : selectedBrandId)
      .then(setDaySlots)
      .catch(() => setDaySlots([]))
      .finally(() => setLoadingSlots(false))
  }, [selectedDay, selectedAccountId, selectedBrandId])

  const loadCalendarData = async () => {
    setLoading(true)
    try {
      const year = currentDate.getFullYear()
      const month = currentDate.getMonth() + 1
      const data = await scheduleService.getCalendar(
        year,
        month,
        selectedAccountId,
        selectedAccountId ? null : selectedBrandId
      )
      setCalendarData(data)
    } catch (error) {
      console.error('Failed to load calendar:', error)
      toast.error('Failed to load calendar data')
    } finally {
      setLoading(false)
    }
  }

  const previousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))
    setSelectedDay(null)
  }

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))
    setSelectedDay(null)
  }

  const monthName = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })

  const getDayStatus = day => {
    if (!day) return null
    if (day.posts_scheduled === day.posts_needed && day.posts_needed > 0) return 'complete'
    if (day.posts_ready > 0) return 'ready'
    if (day.posts_needed > 0) return 'pending'
    return null
  }

  const getStatusIcon = status => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'ready':
        return <Clock className="w-4 h-4 text-yellow-600" />
      case 'pending':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return null
    }
  }

  const getStatusColor = status => {
    switch (status) {
      case 'complete':
        return 'bg-green-50 border-green-200'
      case 'ready':
        return 'bg-yellow-50 border-yellow-200'
      case 'pending':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-white border-gray-200'
    }
  }

  const statusBadgeClass = status => {
    switch (status) {
      case 'scheduled': return 'bg-green-100 text-green-700'
      case 'content_ready': return 'bg-blue-100 text-blue-700'
      case 'posted': return 'bg-gray-100 text-gray-600'
      case 'failed': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const handleDeletePost = async postId => {
    try {
      await scheduleService.deletePost(postId)
      removeScheduledPost(postId)
      setSelectedDay(prev =>
        prev ? { ...prev, posts: prev.posts.filter(p => p.id !== postId) } : prev
      )
      await loadCalendarData()
      toast.success('Scheduled post removed')
    } catch {
      toast.error('Failed to remove post')
    }
  }

  const handleScheduleSuccess = async post => {
    setScheduleModalConfig(null)
    if (selectedDay) {
      const postDate = new Date(post.scheduled_for).toISOString().split('T')[0]
      if (postDate === selectedDay.date) {
        setSelectedDay(prev =>
          prev ? { ...prev, posts: [...(prev.posts || []), post] } : prev
        )
      }
    }
    await loadCalendarData()
  }

  // Build calendar grid
  const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay()
  const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate()
  const calendarDays = []

  // Add empty cells for days before month starts (adjust for Monday start)
  for (let i = 0; i < (firstDay === 0 ? 6 : firstDay - 1); i++) {
    calendarDays.push(null)
  }

  // Add days of month
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const dayData = calendarData.find(d => d.date === dateStr)
    calendarDays.push(
      dayData || { date: dateStr, posts_needed: 0, posts_ready: 0, posts_scheduled: 0, posts: [] }
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{monthName}</h3>
        <div className="flex items-center space-x-2">
          <button onClick={previousMonth} className="p-2 hover:bg-gray-100 rounded-lg">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => { setCurrentDate(new Date()); setSelectedDay(null) }}
            className="px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            Today
          </button>
          <button onClick={nextMonth} className="p-2 hover:bg-gray-100 rounded-lg">
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto" />
        </div>
      )}

      {!loading && (
        <>
          {/* Calendar Grid */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            {/* Day headers */}
            <div className="grid grid-cols-7 bg-gray-50 border-b border-gray-200">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                <div key={day} className="p-2 text-center text-sm font-medium text-gray-700">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar days */}
            <div className="grid grid-cols-7">
              {calendarDays.map((day, index) => {
                if (!day) {
                  return (
                    <div
                      key={`empty-${index}`}
                      className="p-2 border border-gray-100 bg-gray-50 min-h-[80px]"
                    />
                  )
                }

                const status = getDayStatus(day)
                const dayNumber = new Date(day.date + 'T12:00:00').getDate()
                const isToday = day.date === new Date().toISOString().split('T')[0]
                const isSelected = selectedDay?.date === day.date

                return (
                  <div
                    key={day.date}
                    className={`p-2 border border-gray-100 min-h-[80px] cursor-pointer hover:bg-gray-50 transition-colors ${getStatusColor(status)} ${
                      isToday ? 'ring-2 ring-inset ring-primary-500' : ''
                    } ${isSelected ? 'ring-2 ring-inset ring-blue-400' : ''}`}
                    onClick={() => setSelectedDay(isSelected ? null : day)}
                  >
                    <div className="flex items-start justify-between">
                      <span
                        className={`text-sm font-medium ${isToday ? 'text-primary-600' : 'text-gray-900'}`}
                      >
                        {dayNumber}
                      </span>
                      {getStatusIcon(status)}
                    </div>
                    {day.posts_needed > 0 && !compact && (
                      <div className="mt-2 space-y-1">
                        <div className="text-xs text-gray-600">
                          {day.posts_scheduled}/{day.posts_needed} scheduled
                        </div>
                        {day.posts_ready > 0 && day.posts_ready < day.posts_needed && (
                          <div className="text-xs text-yellow-700">{day.posts_ready} ready</div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Selected Day Detail Panel */}
          {selectedDay && !compact && (
            <div className="border border-blue-100 rounded-lg bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-gray-900">
                  {new Date(selectedDay.date + 'T12:00:00').toLocaleDateString('default', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </h4>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setScheduleModalConfig({ initialDate: selectedDay.date })}
                    className="flex items-center space-x-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add Post</span>
                  </button>
                  <button
                    onClick={() => setSelectedDay(null)}
                    className="text-gray-400 hover:text-gray-600 text-2xl leading-none w-6 h-6 flex items-center justify-center"
                  >
                    ×
                  </button>
                </div>
              </div>

              {/* Stats */}
              <div className="flex items-center space-x-6 text-sm mb-4 pb-4 border-b border-gray-100">
                <span className="text-gray-600">
                  Needed: <strong className="text-gray-900">{selectedDay.posts_needed}</strong>
                </span>
                <span className="text-yellow-700">
                  Ready: <strong>{selectedDay.posts_ready}</strong>
                </span>
                <span className="text-green-700">
                  Scheduled: <strong>{selectedDay.posts_scheduled}</strong>
                </span>
              </div>

              {/* Schedule slots from ContentSchedule patterns */}
              {loadingSlots ? (
                <div className="text-xs text-gray-400 py-2">Loading schedule slots…</div>
              ) : daySlots.length > 0 ? (
                <div className="mb-4">
                  <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Schedule Slots
                  </h5>
                  <div className="space-y-1.5">
                    {daySlots.map((slot, i) => (
                      <div
                        key={`${slot.schedule_id}-${slot.slot_time}-${i}`}
                        className={`flex items-center justify-between text-sm rounded-lg px-3 py-2 border transition-colors ${
                          slot.is_taken
                            ? 'bg-green-50 border-green-200'
                            : 'bg-white border-dashed border-gray-300 hover:border-blue-400 hover:bg-blue-50 cursor-pointer'
                        }`}
                        onClick={() => {
                          if (!slot.is_taken) {
                            setScheduleModalConfig({
                              initialDate: selectedDay.date,
                              initialScheduleId: slot.schedule_id,
                              initialSlotTime: slot.slot_time,
                            })
                          }
                        }}
                      >
                        <div className="flex items-center space-x-2">
                          <Clock className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                          <span className="font-medium text-gray-800">{slot.slot_time}</span>
                          <span className="text-xs text-gray-500">{slot.schedule_name}</span>
                        </div>
                        {slot.is_taken ? (
                          <span className="text-xs text-green-600 font-medium">Filled</span>
                        ) : (
                          <span className="text-xs text-blue-500 font-medium flex items-center space-x-1">
                            <Plus className="w-3 h-3" />
                            <span>Assign post</span>
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Existing scheduled posts */}
              {selectedDay.posts.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Scheduled Posts
                  </h5>
                  <div className="space-y-2">
                    {selectedDay.posts.map(post => (
                      <div
                        key={post.id}
                        className="text-sm p-3 bg-gray-50 border border-gray-200 rounded-lg"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-800">
                            {new Date(post.scheduled_for).toLocaleTimeString('default', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                          <div className="flex items-center space-x-2">
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-medium ${statusBadgeClass(post.status)}`}
                            >
                              {post.status.replace('_', ' ')}
                            </span>
                            {post.status !== 'posted' && (
                              <button
                                onClick={e => {
                                  e.stopPropagation()
                                  handleDeletePost(post.id)
                                }}
                                className="text-gray-300 hover:text-red-400 transition-colors"
                                title="Remove scheduled post"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                        {post.caption && (
                          <p className="text-gray-600 mt-1 text-xs line-clamp-2">{post.caption}</p>
                        )}
                        {post.hashtags?.length > 0 && (
                          <p className="text-blue-500 text-xs mt-0.5 truncate">
                            {post.hashtags.map(h => `#${h}`).join(' ')}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty state */}
              {selectedDay.posts.length === 0 && daySlots.length === 0 && !loadingSlots && (
                <div className="text-center py-6 text-gray-400">
                  <Clock className="w-8 h-8 mx-auto mb-2 opacity-40" />
                  <p className="text-sm">No posts or schedule slots for this day.</p>
                  <p className="text-xs mt-1">
                    <a href="/schedules" className="text-blue-500 hover:underline">
                      Create a schedule
                    </a>{' '}
                    to define recurring posting times, or{' '}
                    <button
                      onClick={() => setScheduleModalConfig({ initialDate: selectedDay.date })}
                      className="text-blue-500 hover:underline"
                    >
                      add a post manually
                    </button>
                    .
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Legend */}
          {!compact && (
            <div className="flex items-center justify-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-gray-600">All Scheduled</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-yellow-600" />
                <span className="text-gray-600">Content Ready</span>
              </div>
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-red-600" />
                <span className="text-gray-600">Needs Content</span>
              </div>
            </div>
          )}
        </>
      )}

      {/* Schedule Post Modal (inline from calendar) */}
      {scheduleModalConfig !== null && (
        <SchedulePostModal
          initialDate={scheduleModalConfig.initialDate}
          initialScheduleId={scheduleModalConfig.initialScheduleId || null}
          initialSlotTime={scheduleModalConfig.initialSlotTime || null}
          schedules={schedules}
          accounts={accounts}
          onClose={() => setScheduleModalConfig(null)}
          onSuccess={handleScheduleSuccess}
        />
      )}
    </div>
  )
}
