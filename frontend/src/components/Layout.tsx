import { useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { cn } from '../lib/utils'
import {
  LayoutDashboard,
  FolderKanban,
  Search,
  History,
  Globe,
  Database,
  Code,
  Settings,
  HelpCircle,
  Menu,
  ChevronLeft,
  ChevronRight,
  User,
  LogOut,
  Moon,
  Sun,
  Bell,
  Plus,
} from 'lucide-react'
import { Button } from './ui/Button'
import { useAuthStore } from '../lib/auth'
import { api } from '../lib/api'

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'API Discovery', href: '/projects/new', icon: Search, badge: 'New' },
  { name: 'Runs & History', href: '/runs', icon: History },
  { name: 'API Endpoints', href: '/endpoints', icon: Globe },
  { name: 'Generated Clients', href: '/clients', icon: Code },
  { name: 'Captures & HAR', href: '/captures', icon: Database },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Documentation', href: '/docs', icon: HelpCircle },
]

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const location = useLocation()
  const { user, logout: logoutAction } = useAuthStore()

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout')
    } catch {
      // Ignore errors
    }
    logoutAction()
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/80 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:static z-50 flex h-full flex-col border-r bg-card transition-all duration-300',
          sidebarCollapsed ? 'w-16' : 'w-64',
          !sidebarOpen && 'lg:hidden -translate-x-full'
        )}
        aria-label="Main navigation"
      >
        {/* Logo */}
        <div className={cn('flex h-16 items-center justify-between border-b px-4', sidebarCollapsed && 'justify-center')}>
          {!sidebarCollapsed && (
            <NavLink to="/" className="flex items-center space-x-2" aria-label="Reverse API Engineer">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <Search className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-semibold text-lg">Reverse API Engineer</span>
            </NavLink>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className={cn(sidebarCollapsed && 'ml-auto')}
          >
            {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-1" role="navigation" aria-label="Main">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || 
              (item.href !== '/' && location.pathname.startsWith(item.href))
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  sidebarCollapsed && 'justify-center'
                )}
                aria-current={isActive ? 'page' : undefined}
                title={sidebarCollapsed ? item.name : undefined}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {!sidebarCollapsed && (
                  <>
                    <span>{item.name}</span>
                    {item.badge && (
                      <span className="ml-auto px-1.5 py-0.5 text-xs font-medium bg-primary/20 text-primary rounded-full">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* User section */}
        <div className={cn('border-t p-4', sidebarCollapsed && 'hidden')}>
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
              <User className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name || user?.email}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          </div>
          <div className="flex space-x-2 mt-3">
            <Button variant="ghost" size="sm" className="flex-1" onClick={() => {}}>
              <Settings className="h-4 w-4 mr-2" />
              <span>Profile</span>
            </Button>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60 sticky top-0 z-30">
          <div className="flex h-full items-center justify-between px-4 lg:px-6">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
              <h1 className="text-lg font-semibold hidden sm:block">
                {navigation.find(n => location.pathname === n.href || 
                  (n.href !== '/' && location.pathname.startsWith(n.href)))?.name || 'Dashboard'}
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* Theme toggle */}
              <Button variant="ghost" size="icon" aria-label="Toggle theme">
                <Sun className="h-5 w-5 rotate-90 dark:rotate-0" />
                <Moon className="h-5 w-5 rotate-90 dark:rotate-0" />
              </Button>

              {/* Notifications */}
              <Button variant="ghost" size="icon" aria-label="Notifications">
                <Bell className="h-5 w-5" />
              </Button>

              {/* Quick create */}
              <NavLink to="/projects/new">
                <Button variant="default" size="sm" className="hidden sm:flex">
                  <Plus className="h-4 w-4 mr-2" />
                  New Discovery
                </Button>
              </NavLink>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}