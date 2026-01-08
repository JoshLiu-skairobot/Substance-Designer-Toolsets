import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  FileJson,
  Image,
  Database,
  X,
} from 'lucide-react'
import { navItems } from '@/routes'

const iconMap: Record<string, React.ReactNode> = {
  LayoutDashboard: <LayoutDashboard className="h-5 w-5" />,
  FileJson: <FileJson className="h-5 w-5" />,
  Image: <Image className="h-5 w-5" />,
  Database: <Database className="h-5 w-5" />,
}

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-white transition-transform duration-200 ease-in-out dark:bg-surface-900 lg:static lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between border-b px-4 dark:border-surface-800 lg:hidden">
          <span className="font-semibold">菜单</span>
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-surface-100 dark:hover:bg-surface-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-col gap-1 p-4">
          <p className="mb-2 px-3 text-xs font-medium uppercase text-surface-400">
            功能模块
          </p>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                    : 'text-surface-600 hover:bg-surface-100 hover:text-surface-900 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-white'
                )
              }
            >
              {iconMap[item.icon] || <LayoutDashboard className="h-5 w-5" />}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 border-t p-4 dark:border-surface-800">
          <div className="rounded-lg bg-surface-50 p-3 dark:bg-surface-800">
            <p className="text-xs font-medium text-surface-500 dark:text-surface-400">
              SAT Tools v1.0.0
            </p>
            <p className="mt-1 text-xs text-surface-400 dark:text-surface-500">
              Powered by Substance Automation Toolkit
            </p>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
