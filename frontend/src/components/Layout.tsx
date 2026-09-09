import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Zap, List, AlertCircle, Menu, CheckCircle2, BookOpen, Network } from 'lucide-react'

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-slate-900 text-white transition-all duration-300 overflow-hidden`}>
        <div className="p-4 flex items-center justify-between">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <Zap className="w-8 h-8 text-blue-400" />
              <span className="font-bold text-xl">ResolveIQ</span>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 hover:bg-slate-800 rounded"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

        <nav className="mt-8">
          <NavLink
            to="/"
            icon={<Zap className="w-5 h-5" />}
            label="Dashboard"
            active={isActive('/')}
            collapsed={!sidebarOpen}
          />
          <NavLink
            to="/knowledge"
            icon={<BookOpen className="w-5 h-5" />}
            label="Knowledge"
            active={isActive('/knowledge')}
            collapsed={!sidebarOpen}
          />
          <NavLink
            to="/complaints"
            icon={<List className="w-5 h-5" />}
            label="Complaints"
            active={isActive('/complaints')}
            collapsed={!sidebarOpen}
          />
          <NavLink
            to="/incidents"
            icon={<AlertCircle className="w-5 h-5" />}
            label="Incidents"
            active={isActive('/incidents')}
            collapsed={!sidebarOpen}
          />
          <NavLink
            to="/intelligence-graph"
            icon={<Network className="w-5 h-5" />}
            label="Intelligence Graph"
            active={isActive('/intelligence-graph')}
            collapsed={!sidebarOpen}
          />
          <NavLink
            to="/approval"
            icon={<CheckCircle2 className="w-5 h-5" />}
            label="Approval"
            active={isActive('/approval')}
            collapsed={!sidebarOpen}
          />
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </div>
    </div>
  )
}

type NavLinkProps = {
  to: string
  icon: React.ReactNode
  label: string
  active: boolean
  collapsed: boolean
}

function NavLink({ to, icon, label, active, collapsed }: NavLinkProps) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-4 py-3 transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'text-gray-300 hover:bg-slate-800'
      }`}
      title={collapsed ? label : ''}
    >
      {icon}
      {!collapsed && <span>{label}</span>}
    </Link>
  )
}
