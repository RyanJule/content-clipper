import { Clock, Edit2, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import CreateScheduleModal from '../components/Schedule/CreateScheduleModal'
import ScheduleCard from '../components/Schedule/ScheduleCard'
import { useApi } from '../hooks/useApi'
import { accountService } from '../services/accountService'
import { scheduleService } from '../services/scheduleService'
import { useStore } from '../store'

export default function Schedules() {
  const { schedules, setSchedules, removeSchedule, accounts, setAccounts } = useStore()
  const { loading, execute } = useApi()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState(null)
  const [selectedAccount, setSelectedAccount] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    execute(
      async () => {
        const [schedulesData, accountsData] = await Promise.all([
          scheduleService.getAllSchedules(),
          accountService.getAll(),
        ])
        setSchedules(schedulesData)
        setAccounts(accountsData)
      },
      { errorMessage: 'Failed to load schedules' }
    )
  }

  const handleDelete = async id => {
    if (!window.confirm('Are you sure you want to delete this schedule?')) return

    execute(
      async () => {
        await scheduleService.deleteSchedule(id)
        removeSchedule(id)
      },
      {
        successMessage: 'Schedule deleted successfully',
        errorMessage: 'Failed to delete schedule',
      }
    )
  }

  const handleEdit = schedule => {
    setEditingSchedule(schedule)
    setShowCreateModal(true)
  }

  const filteredSchedules = selectedAccount
    ? schedules.filter(s => s.account_id === selectedAccount)
    : schedules

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Content Schedules</h2>
          <p className="text-gray-600 mt-1">Create and manage posting schedules for your accounts</p>
        </div>
        <button
          onClick={() => {
            setEditingSchedule(null)
            setShowCreateModal(true)
          }}
          className="btn btn-primary flex items-center space-x-2"
          disabled={accounts.length === 0}
        >
          <Plus className="w-5 h-5" />
          <span>New Schedule</span>
        </button>
      </div>

      {accounts.length === 0 ? (
        <div className="card p-12 text-center">
          <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Connect an account first</h3>
          <p className="text-gray-600 mb-6">
            You need to connect at least one social media account before creating schedules
          </p>
          <button
            onClick={() => window.location.href = '/accounts'}
            className="btn btn-primary inline-flex items-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Connect Account</span>
          </button>
        </div>
      ) : (
        <>
          {/* Filter by Account */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Account</label>
            <select
              value={selectedAccount || ''}
              onChange={e => setSelectedAccount(e.target.value ? parseInt(e.target.value) : null)}
              className="input max-w-xs"
            >
              <option value="">All Accounts</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.platform} - @{account.account_username}
                </option>
              ))}
            </select>
          </div>

          {loading && schedules.length === 0 ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <p className="text-gray-600 mt-4">Loading schedules...</p>
            </div>
          ) : filteredSchedules.length === 0 ? (
            <div className="card p-12 text-center">
              <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {selectedAccount ? 'No schedules for this account' : 'No schedules yet'}
              </h3>
              <p className="text-gray-600 mb-6">
                {selectedAccount
                  ? 'Create a posting schedule for this account'
                  : 'Create your first posting schedule to automate content'}
              </p>
              <button
                onClick={() => {
                  setEditingSchedule(null)
                  setShowCreateModal(true)
                }}
                className="btn btn-primary inline-flex items-center space-x-2"
              >
                <Plus className="w-5 h-5" />
                <span>Create Schedule</span>
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredSchedules.map(schedule => {
                const account = accounts.find(a => a.id === schedule.account_id)
                return (
                  <div key={schedule.id} className="card p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          {account && (
                            <span className="text-sm text-gray-600">
                              {account.platform} - @{account.account_username}
                            </span>
                          )}
                        </div>
                        <ScheduleCard schedule={schedule} />
                      </div>

                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => handleEdit(schedule)}
                          className="btn btn-secondary text-sm"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(schedule.id)}
                          className="btn btn-danger text-sm"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {showCreateModal && (
        <CreateScheduleModal
          schedule={editingSchedule}
          accounts={accounts}
          onClose={() => {
            setShowCreateModal(false)
            setEditingSchedule(null)
          }}
          onSuccess={() => {
            setShowCreateModal(false)
            setEditingSchedule(null)
            loadData()
          }}
        />
      )}
    </div>
  )
}