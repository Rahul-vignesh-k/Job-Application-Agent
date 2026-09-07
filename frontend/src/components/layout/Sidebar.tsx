import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Briefcase, FileText, BarChart3,
  FileSearch, MessageSquarePlus, History, Settings,
  Zap, ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV = [
  { to: '/',            icon: LayoutDashboard,  label: 'Dashboard' },
  { to: '/jobs',        icon: Briefcase,         label: 'Job Queue' },
  { to: '/resumes',     icon: FileText,          label: 'Resumes' },
  { to: '/match',       icon: BarChart3,         label: 'Match Report' },
  { to: '/preview',     icon: FileSearch,        label: 'Resume Preview' },
  { to: '/input',       icon: MessageSquarePlus, label: 'Manual Input' },
  { to: '/history',     icon: History,           label: 'History' },
  { to: '/settings',    icon: Settings,          label: 'Settings' },
]

export function Sidebar() {
  const location = useLocation()
  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-card/80 backdrop-blur-xl">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20 ring-1 ring-primary/40">
          <Zap className="h-4 w-4 text-primary" />
        </div>
        <div>
          <p className="text-sm font-bold tracking-wide text-foreground">JobAgent</p>
          <p className="text-[10px] text-muted-foreground tracking-widest uppercase">AI Powered</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => {
          const active = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to)
          return (
            <NavLink
              key={to}
              to={to}
              className={cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150',
                active
                  ? 'bg-primary/15 text-primary ring-1 ring-primary/20'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              )}
            >
              <Icon className={cn('h-4 w-4 shrink-0', active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground')} />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight className="h-3 w-3 text-primary/60" />}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-border px-4 py-3">
        <p className="text-[11px] text-muted-foreground text-center">
          Powered by Gemini + ChromaDB
        </p>
      </div>
    </aside>
  )
}
