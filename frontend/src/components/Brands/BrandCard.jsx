import { Instagram, Music2, Pencil, Trash2, Youtube } from 'lucide-react'

const PLATFORM_META = {
  instagram: { icon: Instagram, color: 'bg-pink-500', label: 'Instagram' },
  youtube: { icon: Youtube, color: 'bg-red-600', label: 'YouTube' },
  tiktok: { icon: Music2, color: 'bg-black', label: 'TikTok' },
}

export default function BrandCard({ brand, onEdit, onDelete, onConnectAccount }) {
  const connectedPlatforms = brand.accounts.map(a => a.platform)
  const allPlatforms = ['instagram', 'youtube', 'tiktok']

  return (
    <div className="card p-6 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {brand.logo_url ? (
            <img
              src={brand.logo_url}
              alt={brand.name}
              className="w-12 h-12 rounded-full object-cover border border-gray-200"
            />
          ) : (
            <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
              <span className="text-primary-600 font-bold text-lg">
                {brand.name.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
          <div>
            <h3 className="font-semibold text-gray-900 text-lg">{brand.name}</h3>
            {brand.description && (
              <p className="text-sm text-gray-500 mt-0.5 line-clamp-1">{brand.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onEdit(brand)}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            title="Edit brand"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(brand)}
            className="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50"
            title="Delete brand"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Connected accounts */}
      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
          Connected Accounts
        </p>
        <div className="space-y-2">
          {allPlatforms.map(platform => {
            const meta = PLATFORM_META[platform]
            const account = brand.accounts.find(a => a.platform === platform)
            const Icon = meta.icon

            return (
              <div
                key={platform}
                className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-gray-50"
              >
                <div className="flex items-center gap-2">
                  <div className={`${meta.color} p-1.5 rounded text-white`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">{meta.label}</span>
                  {account && (
                    <span className="text-xs text-gray-500">@{account.account_username}</span>
                  )}
                </div>
                {account ? (
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      account.is_active
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {account.is_active ? 'Connected' : 'Inactive'}
                  </span>
                ) : (
                  <button
                    onClick={() => onConnectAccount(brand, platform)}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                  >
                    + Connect
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
