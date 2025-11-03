import { AlertCircle, CheckCircle, ChevronLeft, ChevronRight, Clock } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { scheduleService } from '../../services/scheduleService'
import { useStore } from '../../store'

export default function CalendarView({ compact = false, currentMonth: initialMonth }) {
  const { selectedAccountId, calendarData, setCalendarData } = useStore()
  const [currentDate, setCurrentDate] = useState(initialMonth || new Date())
  const [loading, setLoading] = useState(false)
  const [selectedDay, setSelectedDay] = useState(null)

  useEffect(() => {
    loadCalendarData()
  }, [currentDate, selectedAccountId])

  const loadCalendarData = async () => {
    setLoading(true)
    try {
      const year = currentDate.getFullYear()
      const month = currentDate.getMonth() + 1
      const data = await scheduleService.getCalendar(year, month, selectedAccountId)
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
  }

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))
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
    calendarDays.push(dayData || { date: dateStr, posts_needed: 0, posts_ready: 0, posts_scheduled: 0, posts: [] })
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
            onClick={() => setCurrentDate(new Date())}
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
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
                  return <div key={`empty-${index}`} className="p-2 border border-gray-100 bg-gray-50 min-h-[80px]" />
                }

                const status = getDayStatus(day)
                const dayNumber = new Date(day.date).getDate()
                const isToday = day.date === new Date().toISOString().split('T')[0]

                return (
                  <div
                    key={day.date}
                    className={`p-2 border border-gray-100 min-h-[80px] cursor-pointer hover:bg-gray-50 transition-colors ${getStatusColor(status)} ${
                      isToday ? 'ring-2 ring-primary-500' : ''
                    }`}
                    onClick={() => setSelectedDay(day)}
                  >
                    <div className="flex items-start justify-between">
                      <span className={`text-sm font-medium ${isToday ? 'text-primary-600' : 'text-gray-900'}`}>
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

          {/* Selected Day Details */}
          {selectedDay && !compact && (
            <div className="card p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-gray-900">
                  {new Date(selectedDay.date).toLocaleDateString('default', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </h4>
                <button onClick={() => setSelectedDay(null)} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">
                  ×
                </button>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Posts Needed:</span>
                  <span className="font-medium">{selectedDay.posts_needed}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Content Ready:</span>
                  <span className="font-medium text-yellow-600">{selectedDay.posts_ready}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Scheduled:</span>
                  <span className="font-medium text-green-600">{selectedDay.posts_scheduled}</span>
                </div>
              </div>

              {selectedDay.posts.length > 0 && (
                <div className="mt-4">
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Scheduled Posts:</h5>
                  <div className="space-y-2">
                    {selectedDay.posts.map(post => (
                      <div key={post.id} className="text-sm p-2 bg-gray-50 rounded">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">
                            {new Date(post.scheduled_for).toLocaleTimeString('default', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-xs ${
                              post.status === 'scheduled'
                                ? 'bg-green-100 text-green-700'
                                : post.status === 'content_ready'
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {post.status}
                          </span>
                        </div>
                        {post.caption && (
                          <p className="text-gray-600 mt-1 text-xs truncate">{post.caption}</p>
                        )}
                      </div>
                    ))}
                  </div>
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
    </div>
  )
}