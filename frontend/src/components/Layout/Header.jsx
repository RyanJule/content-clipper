import { Bell, Settings, User } from 'lucide-react'

export default function Header() {
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Content Clipper</h1>
        <p className="text-sm text-gray-500">AI-powered video clipping and scheduling</p>
      </div>

      <div className="flex items-center space-x-4">
        <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
          <Bell className="w-5 h-5" />
        </button>
        <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
          <Settings className="w-5 h-5" />
        </button>
        <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
          <User className="w-5 h-5" />
        </button>
      </div>
    </header>
  )
}