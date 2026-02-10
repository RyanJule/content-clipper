import clsx from 'clsx'
import { Calendar, ChevronLeft, ChevronRight, Clock, Home, Instagram, Linkedin, Scissors, Share2, Users, Video, Youtube } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useStore } from '../../store'

const navigation = [
  { name: 'Dashboard', to: '/dashboard', icon: Home },
  { name: 'Accounts', to: '/accounts', icon: Users },
  { name: 'Schedules', to: '/schedules', icon: Clock },
  { name: 'Calendar', to: '/calendar', icon: Calendar },
  { name: 'Media Library', to: '/media', icon: Video },
  { name: 'Clips', to: '/clips', icon: Scissors },
  { name: 'Social Posts', to: '/social', icon: Share2 },
  { name: 'YouTube Studio', to: '/youtube', icon: Youtube },
  { name: 'Instagram', to: '/instagram', icon: Instagram },
  { name: 'LinkedIn', to: '/linkedin', icon: Linkedin },
]

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useStore()

  return (
    <div
      className={clsx(
        'fixed left-0 top-0 h-full bg-white border-r border-gray-200 transition-all z-30',
        sidebarOpen ? 'w-64' : 'w-20'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
        {sidebarOpen && (
          <div className="flex items-center space-x-2">
            <Scissors className="w-8 h-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">Clipper</span>
          </div>
        )}
        {!sidebarOpen && <Scissors className="w-8 h-8 text-primary-600 mx-auto" />}
      </div>

      {/* Navigation */}
      <nav className="mt-6 px-3 space-y-1">
        {navigation.map(item => (
          <NavLink
            key={item.name}
            to={item.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center px-3 py-2 rounded-lg transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-700 hover:bg-gray-100',
                !sidebarOpen && 'justify-center'
              )
            }
            title={!sidebarOpen ? item.name : undefined}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span className="ml-3 font-medium">{item.name}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Toggle Button */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 bg-white border border-gray-200 rounded-full p-1 hover:bg-gray-50 shadow-sm"
      >
        {sidebarOpen ? (
          <ChevronLeft className="w-4 h-4 text-gray-600" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-600" />
        )}
      </button>
    </div>
  )
}