import { forwardRef, InputHTMLAttributes, useState, useCallback } from 'react'
import { clsx } from 'clsx'
import { Search, X } from 'lucide-react'

export interface SearchInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  value?: string
  onChange?: (value: string) => void
  onSearch?: (value: string) => void
  debounceMs?: number
  showClearButton?: boolean
}

const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  (
    {
      className,
      value: controlledValue,
      onChange,
      onSearch,
      debounceMs = 300,
      showClearButton = true,
      placeholder = '搜索...',
      ...props
    },
    ref
  ) => {
    const [internalValue, setInternalValue] = useState('')
    const value = controlledValue !== undefined ? controlledValue : internalValue

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value
        if (controlledValue === undefined) {
          setInternalValue(newValue)
        }
        onChange?.(newValue)

        // Debounced search
        if (onSearch) {
          const timeoutId = setTimeout(() => {
            onSearch(newValue)
          }, debounceMs)
          return () => clearTimeout(timeoutId)
        }
      },
      [controlledValue, onChange, onSearch, debounceMs]
    )

    const handleClear = () => {
      if (controlledValue === undefined) {
        setInternalValue('')
      }
      onChange?.('')
      onSearch?.('')
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        onSearch?.(value)
      }
      if (e.key === 'Escape') {
        handleClear()
      }
    }

    return (
      <div className={clsx('relative', className)}>
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-400" />
        <input
          ref={ref}
          type="text"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={clsx(
            'w-full rounded-lg border bg-white py-2 pl-10 pr-10 text-sm',
            'placeholder:text-surface-400',
            'focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500',
            'dark:bg-surface-900 dark:border-surface-700 dark:text-white'
          )}
          {...props}
        />
        {showClearButton && value && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-0.5 text-surface-400 hover:bg-surface-100 hover:text-surface-600 dark:hover:bg-surface-800"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    )
  }
)

SearchInput.displayName = 'SearchInput'

export default SearchInput
