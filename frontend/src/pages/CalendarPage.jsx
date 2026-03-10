import { Filter, Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CalendarView from '../components/Calendar/CalendarView'
import { accountService } from '../services/accountService'
import { scheduleService } from '../services/scheduleService'
import { useStore } from '../store'

export default function CalendarPage() {
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
  const navigate = useNavigate()

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
      const data = await scheduleService.getAllSchedules(
        null,
        selectedBrandId || null
      )
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
              <Filter className="w-5 h-5 text-gray-500" />
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
            className="flex items-center space-x-1.5 btn btn-secondary text-sm"
          >
            <Plus className="w-4 h-4" />
            <span>New Schedule</span>
          </button>
        </div>
      </div>

      {schedules.length === 0 && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
          <strong>No posting schedules yet.</strong> Create a schedule to define recurring posting
          times — they'll appear as slots on the calendar that you can fill with content.{' '}
          <button
            onClick={() => navigate('/schedules')}
            className="underline font-medium hover:text-blue-900"
          >
            Create a schedule
          </button>
        </div>
      )}

      <div className="card p-6">
        <CalendarView compact={false} currentMonth={currentMonth} />
      </div>
    </div>
  )
}
