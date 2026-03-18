import { CalendarDays, Filter, Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CalendarView from '../components/Calendar/CalendarView'
import { accountService } from '../services/accountService'
import { scheduleService } from '../services/scheduleService'
import { useStore } from '../store'

export default function CalendarPage() {
  const navigate = useNavigate()
  const {
    accounts,
    setAccounts,
    schedules,
    setSchedules,
    selectedAccountId,
    setSelectedAccountId,
    selectedBrandId,
  } = useStore()
  const [currentMonth] = useState(new Date())

  const brandAccounts = selectedBrandId
    ? accounts.filter(a => a.brand_id === selectedBrandId)
    : accounts

  useEffect(() => {
    loadAccounts()
    loadSchedules()
  }, [])

  const loadAccounts = async () => {
    try {
      const data = await accountService.getAll()
      setAccounts(data)
    } catch (error) {
      console.error('Failed to load accounts:', error)
    }
  }

  const loadSchedules = async () => {
    try {
      const data = await scheduleService.getAllSchedules()
      setSchedules(data)
    } catch (error) {
      console.error('Failed to load schedules:', error)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Content Calendar</h2>
          <p className="text-gray-600 mt-1">View and manage your scheduled posts</p>
        </div>

        <div className="flex items-center space-x-3">
          {brandAccounts.length > 0 && (
            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5 text-gray-600" />
              <select
                value={selectedAccountId || ''}
                onChange={e => setSelectedAccountId(e.target.value ? parseInt(e.target.value) : null)}
                className="input max-w-xs"
              >
                <option value="">All Accounts</option>
                {brandAccounts.map(account => (
                  <option key={account.id} value={account.id}>
                    {account.platform} - @{account.account_username}
                  </option>
                ))}
              </select>
            </div>
          )}
          <button
            onClick={() => navigate('/schedules')}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>New Schedule</span>
          </button>
        </div>
      </div>

      {schedules.length === 0 && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start space-x-3">
          <CalendarDays className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-800">No schedules yet</p>
            <p className="text-sm text-blue-700 mt-0.5">
              Create a content schedule to define which days and times to post, then use the
              calendar to fill those slots.{' '}
              <button
                onClick={() => navigate('/schedules')}
                className="underline font-medium"
              >
                Create a schedule →
              </button>
            </p>
          </div>
        </div>
      )}

      <div className="card p-6">
        <CalendarView compact={false} currentMonth={currentMonth} />
      </div>
    </div>
  )
}
