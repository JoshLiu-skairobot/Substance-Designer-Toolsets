import { ReactNode } from 'react'
import { clsx } from 'clsx'

export interface Column<T> {
  key: string
  header: string
  width?: string
  align?: 'left' | 'center' | 'right'
  render?: (value: unknown, row: T, index: number) => ReactNode
}

export interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  loading?: boolean
  emptyMessage?: string
  onRowClick?: (row: T, index: number) => void
  rowKey?: keyof T | ((row: T) => string)
  className?: string
  striped?: boolean
  hoverable?: boolean
}

function Table<T extends Record<string, unknown>>({
  columns,
  data,
  loading = false,
  emptyMessage = '暂无数据',
  onRowClick,
  rowKey = 'id',
  className,
  striped = false,
  hoverable = true,
}: TableProps<T>) {
  const getRowKey = (row: T, index: number): string => {
    if (typeof rowKey === 'function') {
      return rowKey(row)
    }
    return String(row[rowKey] ?? index)
  }

  const getCellValue = (row: T, column: Column<T>, index: number): ReactNode => {
    const value = row[column.key]
    if (column.render) {
      return column.render(value, row, index)
    }
    return String(value ?? '')
  }

  return (
    <div className={clsx('overflow-hidden rounded-lg border dark:border-surface-800', className)}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-surface-200 dark:divide-surface-800">
          <thead className="bg-surface-50 dark:bg-surface-800/50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  style={{ width: column.width }}
                  className={clsx(
                    'px-4 py-3 text-xs font-medium uppercase tracking-wider text-surface-500 dark:text-surface-400',
                    {
                      'text-left': column.align === 'left' || !column.align,
                      'text-center': column.align === 'center',
                      'text-right': column.align === 'right',
                    }
                  )}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-200 bg-white dark:divide-surface-800 dark:bg-surface-900">
            {loading ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-surface-500"
                >
                  <div className="flex items-center justify-center gap-2">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
                    加载中...
                  </div>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-surface-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, index) => (
                <tr
                  key={getRowKey(row, index)}
                  onClick={() => onRowClick?.(row, index)}
                  className={clsx(
                    onRowClick && 'cursor-pointer',
                    striped && index % 2 === 1 && 'bg-surface-50 dark:bg-surface-800/30',
                    hoverable && 'hover:bg-surface-50 dark:hover:bg-surface-800/50'
                  )}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={clsx(
                        'px-4 py-3 text-sm text-surface-900 dark:text-surface-100',
                        {
                          'text-left': column.align === 'left' || !column.align,
                          'text-center': column.align === 'center',
                          'text-right': column.align === 'right',
                        }
                      )}
                    >
                      {getCellValue(row, column, index)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Table
