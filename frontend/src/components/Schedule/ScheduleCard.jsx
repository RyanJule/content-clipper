import { Calendar, Clock, Edit2, TrendingUp } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export default function ScheduleCard({ schedule, compact = false }) {
  const navigate = useNavigate()

  return (
    <div className="card p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <h4 className="font-semibold text-gray-900">{schedule.name}</h4>
            {schedule.is_active && (
              <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">
                Active
              </span>
            )}
          </div>
          {schedule.description && (
            <p className="text-sm text-gray-600 mt-1">{schedule.description}</p>
          )}

          <div className="mt-3 space-y-2">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Calendar className="w-4 h-4" />
              <span>
                {schedule.days_of_week.map(d => dayNames[d]).join(', ')}
              </span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>{schedule.posting_times.join(', ')}</span>
            </div>
            {(schedule.engagement_score || schedule.growth_rate) && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <TrendingUp className="w-4 h-4" />
                <span>
                  {schedule.engagement_score && `${schedule.engagement_score}% engagement`}
                  {schedule.engagement_score && schedule.growth_rate && ' • '}
                  {schedule.growth_rate && `${schedule.growth_rate}% growth`}
                </span>
              </div>
            )}
          </div>
        </div>

        {!compact && (
          <button
            onClick={() => navigate(`/schedules/${schedule.id}/edit`)}
            className="btn btn-secondary text-sm"
          >
            <Edit2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}