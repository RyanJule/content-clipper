import { Instagram, Linkedin, Music2, TrendingUp, Twitter, Youtube } from 'lucide-react'

const platformIcons = {
  instagram: Instagram,
  twitter: Twitter,
  linkedin: Linkedin,
  youtube: Youtube,
  tiktok: Music2,
}

const platformColors = {
  instagram: 'bg-pink-500',
  twitter: 'bg-blue-400',
  linkedin: 'bg-blue-700',
  youtube: 'bg-red-600',
  tiktok: 'bg-black',
}

export default function AccountCard({ account, compact = false }) {
  const Icon = platformIcons[account.platform] || TrendingUp
  const colorClass = platformColors[account.platform] || 'bg-gray-500'

  return (
    <div className="card p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start space-x-3">
        <div className={`${colorClass} p-2 rounded-lg text-white`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 capitalize">{account.platform}</h4>
          <p className="text-sm text-gray-600">@{account.account_username}</p>
          {!compact && (
            <div className="mt-2">
              <span
                className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                  account.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                }`}
              >
                {account.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}