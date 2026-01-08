import { Moon, Sun, Menu } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'

interface HeaderProps {
  onMenuClick?: () => void
}

const Header = ({ onMenuClick }: HeaderProps) => {
  const { theme, toggleTheme } = useThemeStore()

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b bg-white px-4 dark:bg-surface-900 dark:border-surface-800">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="rounded-lg p-2 hover:bg-surface-100 dark:hover:bg-surface-800 lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-primary-700">
            <span className="text-lg font-bold text-white">S</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-surface-900 dark:text-white">
              SAT Tools
            </h1>
            <p className="text-xs text-surface-500 dark:text-surface-400">
              Substance Automation Toolkit
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-surface-500 hover:bg-surface-100 hover:text-surface-900 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-white"
          title={theme === 'dark' ? '切换到亮色模式' : '切换到暗色模式'}
        >
          {theme === 'dark' ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </button>
      </div>
    </header>
  )
}

export default Header
