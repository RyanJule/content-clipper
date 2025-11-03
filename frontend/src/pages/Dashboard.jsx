import {
  Calendar as CalendarIcon,
  Clock,
  Plus,
  TrendingUp,
  Users
} from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import AccountCard from '../components/Accounts/AccountCard'
import CalendarView from '../components/Calendar/CalendarView'
import ScheduleCard from '../components/Schedule/ScheduleCard'
import { accountService } from '../services/accountService'
import { clipService } from '../services/clipService'
import { mediaService } from '../services/mediaService'
import { scheduleService } from '../services/scheduleService'
import { useStore } from '../store'

export default function Dashboard() {
  const navigate = useNavigate()
  const { accounts, setAccounts, schedules, setSchedules, selectedAccountId } = useStore()
  const [stats, setStats] = useState({
    totalAccounts: 0,
    activeSchedules: 0,
    postsThisWeek: 0,
    avgEngagement: 0,
  })
  const [loading, setLoading] = useState(true)
  const [currentMonth, setCurrentMonth] = useState(new Date())

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      const [accountsData, schedulesData, mediaData, clipsData] = await Promise.all([
        accountService.getAll().catch(() => []),
        scheduleService.getAllSchedules().catch(() => []),
        mediaService.getAll().catch(() => []),
        clipService.getAll().catch(() => []),
      ])

      setAccounts(accountsData)
      setSchedules(schedulesData)

      setStats({
        totalAccounts: accountsData.length,
        activeSchedules: schedulesData.filter(s => s.is_active).length,
        postsThisWeek: 0, // TODO: Calculate from calendar
        avgEngagement: 0, // TODO: Calculate from posts
      })
    } catch (error) {
      console.error('Failed to load dashboard:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const statCards = [
    {
      name: 'Connected Accounts',
      value: stats.totalAccounts,
      icon: Users,
      color: 'bg-blue-500',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600',
      action: () => navigate('/accounts'),
    },
    {
      name: 'Active Schedules',
      value: stats.activeSchedules,
      icon: Clock,
      color: 'bg-purple-500',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600',
      action: () => navigate('/schedules'),
    },
    {
      name: 'Posts This Week',
      value: stats.postsThisWeek,
      icon: CalendarIcon,
      color: 'bg-green-500',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600',
    },
    {
      name: 'Avg Engagement',
      value: `${stats.avgEngagement}%`,
      icon: TrendingUp,
      color: 'bg-orange-500',
      bgColor: 'bg-orange-50',
      textColor: 'text-orange-600',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-600 mt-1">Manage your content schedule and connected accounts</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map(stat => (
          <div
            key={stat.name}
            className={`card p-6 ${stat.action ? 'cursor-pointer hover:shadow-md' : ''} transition-shadow`}
            onClick={stat.action}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">{stat.name}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
              </div>
              <div className={`${stat.bgColor} p-3 rounded-lg`}>
                <stat.icon className={`w-6 h-6 ${stat.textColor}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Connected Accounts Section */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900">Connected Accounts</h3>
          <button
            onClick={() => navigate('/accounts')}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Connect Account</span>
          </button>
        </div>

        {accounts.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-semibold text-gray-900 mb-2">No accounts connected</h4>
            <p className="text-gray-600 mb-6">Connect your social media accounts to start scheduling</p>
            <button
              onClick={() => navigate('/accounts')}
              className="btn btn-primary inline-flex items-center space-x-2"
            >
              <Plus className="w-5 h-5" />
              <span>Connect First Account</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {accounts.slice(0, 3).map(account => (
              <AccountCard key={account.id} account={account} />
            ))}
            {accounts.length > 3 && (
              <button
                onClick={() => navigate('/accounts')}
                className="card p-6 flex items-center justify-center text-gray-600 hover:text-primary-600 hover:border-primary-300 transition-colors"
              >
                <span className="text-sm font-medium">View all {accounts.length} accounts →</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Calendar View */}
      {accounts.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-900">Content Calendar</h3>
            <button
              onClick={() => navigate('/calendar')}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              View Full Calendar →
            </button>
          </div>
          <CalendarView compact={true} currentMonth={currentMonth} />
        </div>
      )}

      {/* Active Schedules */}
      {schedules.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-900">Active Schedules</h3>
            <button
              onClick={() => navigate('/schedules')}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <Plus className="w-5 h-5" />
              <span>New Schedule</span>
            </button>
          </div>
          <div className="space-y-3">
            {schedules.slice(0, 3).map(schedule => (
              <ScheduleCard key={schedule.id} schedule={schedule} compact={true} />
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/media')}
            className="btn btn-secondary flex items-center justify-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Upload Content</span>
          </button>
          <button
            onClick={() => navigate('/clips')}
            className="btn btn-secondary flex items-center justify-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Create Clip</span>
          </button>
          <button
            onClick={() => navigate('/schedules')}
            className="btn btn-secondary flex items-center justify-center space-x-2"
          >
            <CalendarIcon className="w-5 h-5" />
            <span>Plan Schedule</span>
          </button>
        </div>
      </div>
    </div>
  )
}