import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Toaster } from '@/components/ui/toaster'

export function Layout() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64 overflow-auto">
        <div className="min-h-screen p-8">
          <Outlet />
        </div>
      </main>
      <Toaster />
    </div>
  )
}
