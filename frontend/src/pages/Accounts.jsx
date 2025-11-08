// frontend/src/pages/Accounts.jsx
import { CheckCircle, Plus, Settings, Trash2, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import AccountCard from '../components/Accounts/AccountCard'
import OAuthConnectModal from '../components/Accounts/OAuthConnectModal'
import { useApi } from '../hooks/useApi'
import { accountService } from '../services/accountService'
import { useStore } from '../store'

export default function Accounts() {
  const { accounts, setAccounts, removeAccount } = useStore()
  const { loading, execute } = useApi()
  const [showConnectModal, setShowConnectModal] = useState(false)

  const loadAccounts = async () => {
    execute(
      async () => {
        const data = await accountService.getAll()
        setAccounts(data)
      },
      { errorMessage: 'Failed to load accounts' }
    )
  }

  useEffect(() => {
    loadAccounts()
  }, [])

  const handleDelete = async id => {
    if (!window.confirm('Are you sure you want to disconnect this account?')) return

    execute(
      async () => {
        await accountService.delete(id)
        removeAccount(id)
      },
      {
        successMessage: 'Account disconnected successfully',
        errorMessage: 'Failed to disconnect account',
      }
    )
  }

  const handleToggleActive = async (id, isActive) => {
    execute(
      async () => {
        await accountService.update(id, { is_active: !isActive })
        await loadAccounts()
      },
      {
        successMessage: isActive ? 'Account deactivated' : 'Account activated',
        errorMessage: 'Failed to update account',
      }
    )
  }

  const handleOAuthSuccess = async () => {
    // Reload accounts after successful OAuth
    await loadAccounts()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Connected Accounts</h2>
          <p className="text-gray-600 mt-1">Manage your social media account connections</p>
        </div>
        <button
          onClick={() => setShowConnectModal(true)}
          className="btn btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Connect Account</span>
        </button>
      </div>

      {loading && accounts.length === 0 ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading accounts...</p>
        </div>
      ) : accounts.length === 0 ? (
        <div className="card p-12 text-center">
          <Settings className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No accounts connected</h3>
          <p className="text-gray-600 mb-6">
            Connect your social media accounts to start scheduling content
          </p>
          <button
            onClick={() => setShowConnectModal(true)}
            className="btn btn-primary inline-flex items-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Connect First Account</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map(account => (
            <div key={account.id} className="card overflow-hidden">
              <div className="p-6">
                <AccountCard account={account} />

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="text-xs text-gray-500 mb-3">
                    Connected {new Date(account.connected_at).toLocaleDateString()}
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleToggleActive(account.id, account.is_active)}
                      className={`flex-1 btn text-sm py-2 ${
                        account.is_active ? 'btn-secondary' : 'btn-primary'
                      }`}
                    >
                      {account.is_active ? (
                        <>
                          <XCircle className="w-4 h-4 inline mr-1" />
                          Deactivate
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-4 h-4 inline mr-1" />
                          Activate
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(account.id)}
                      className="btn btn-danger text-sm py-2 px-3"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showConnectModal && (
        <OAuthConnectModal
          onClose={() => setShowConnectModal(false)}
          onSuccess={handleOAuthSuccess}
        />
      )}
    </div>
  )
}