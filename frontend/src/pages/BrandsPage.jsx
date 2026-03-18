import { Briefcase, Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import BrandCard from '../components/Brands/BrandCard'
import BrandFormModal from '../components/Brands/BrandFormModal'
import OAuthConnectModal from '../components/Accounts/OAuthConnectModal'
import { useApi } from '../hooks/useApi'
import { brandService } from '../services/brandService'
import { useStore } from '../store'

export default function BrandsPage() {
  const { brands, setBrands, addBrand, updateBrand, removeBrand } = useStore()
  const { loading, execute } = useApi()

  const [showFormModal, setShowFormModal] = useState(false)
  const [editingBrand, setEditingBrand] = useState(null)
  const [formLoading, setFormLoading] = useState(false)

  // State for connecting an account to a specific brand
  const [connectingBrand, setConnectingBrand] = useState(null)
  const [connectingPlatform, setConnectingPlatform] = useState(null)

  const loadBrands = () =>
    execute(async () => {
      const data = await brandService.getAll()
      setBrands(data)
    }, { errorMessage: 'Failed to load brands' })

  useEffect(() => {
    loadBrands()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleCreate = async payload => {
    setFormLoading(true)
    try {
      const brand = await brandService.create(payload)
      addBrand(brand)
      toast.success('Brand created!')
      setShowFormModal(false)
    } catch {
      toast.error('Failed to create brand')
    } finally {
      setFormLoading(false)
    }
  }

  const handleEdit = brand => {
    setEditingBrand(brand)
    setShowFormModal(true)
  }

  const handleUpdate = async payload => {
    setFormLoading(true)
    try {
      const updated = await brandService.update(editingBrand.id, payload)
      updateBrand(editingBrand.id, updated)
      toast.success('Brand updated!')
      setShowFormModal(false)
      setEditingBrand(null)
    } catch {
      toast.error('Failed to update brand')
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async brand => {
    if (!window.confirm(`Delete brand "${brand.name}"? Connected accounts will be unlinked.`)) return
    try {
      await brandService.delete(brand.id)
      removeBrand(brand.id)
      toast.success('Brand deleted')
    } catch {
      toast.error('Failed to delete brand')
    }
  }

  const handleConnectAccount = (brand, platform) => {
    setConnectingBrand(brand)
    setConnectingPlatform(platform)
  }

  const handleOAuthSuccess = () => {
    // Reload brands to pick up newly connected account
    loadBrands()
    setConnectingBrand(null)
    setConnectingPlatform(null)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Brands</h2>
          <p className="text-gray-600 mt-1">
            Manage your brands and their social media accounts
          </p>
        </div>
        <button
          onClick={() => {
            setEditingBrand(null)
            setShowFormModal(true)
          }}
          className="btn btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>New Brand</span>
        </button>
      </div>

      {loading && brands.length === 0 ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
          <p className="text-gray-600 mt-4">Loading brands...</p>
        </div>
      ) : brands.length === 0 ? (
        <div className="card p-12 text-center">
          <Briefcase className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No brands yet</h3>
          <p className="text-gray-600 mb-6">
            Create a brand to organize your social media accounts and content
          </p>
          <button
            onClick={() => setShowFormModal(true)}
            className="btn btn-primary inline-flex items-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Create First Brand</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {brands.map(brand => (
            <BrandCard
              key={brand.id}
              brand={brand}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onConnectAccount={handleConnectAccount}
            />
          ))}
        </div>
      )}

      {showFormModal && (
        <BrandFormModal
          brand={editingBrand}
          loading={formLoading}
          onClose={() => {
            setShowFormModal(false)
            setEditingBrand(null)
          }}
          onSubmit={editingBrand ? handleUpdate : handleCreate}
        />
      )}

      {connectingBrand && (
        <OAuthConnectModal
          brandId={connectingBrand.id}
          initialPlatform={connectingPlatform}
          onClose={() => {
            setConnectingBrand(null)
            setConnectingPlatform(null)
          }}
          onSuccess={handleOAuthSuccess}
        />
      )}
    </div>
  )
}
