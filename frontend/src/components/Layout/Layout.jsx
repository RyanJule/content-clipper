import { Outlet } from 'react-router-dom'
import { useStore } from '../../store'
import Header from './Header'
import Sidebar from './Sidebar'

export default function Layout() {
  const sidebarOpen = useStore(state => state.sidebarOpen)

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className={`flex-1 flex flex-col transition-all ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}