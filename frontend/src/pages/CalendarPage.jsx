import { Filter } from 'lucide-react'
import { useEffect, useState } from 'react'
import CalendarView from '../components/Calendar/CalendarView'
import { accountService } from '../services/accountService'
import { useStore } from '../store'

export default function CalendarPage() {
  const { accounts, setAccounts, selectedAccountId, setSelectedAccountId, selectedBrandId } = useStore()
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const brandAccounts = selectedBrandId
    ? accounts.filter(a => a.brand_id === selectedBrandId)
    : accounts

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      const data = await accountService.getAll()
      setAccounts(data)
    } catch (error) {
      console.error('Failed to load accounts:', error)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Content Calendar</h2>
          <p className="text-gray-600 mt-1">View and manage your scheduled posts</p>
        </div>

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
      </div>

      <div className="card p-6">
        <CalendarView compact={false} currentMonth={currentMonth} />
      </div>
    </div>
  )
}