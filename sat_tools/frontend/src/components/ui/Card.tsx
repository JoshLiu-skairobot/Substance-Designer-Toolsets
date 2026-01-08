import { HTMLAttributes, forwardRef } from 'react'
import { clsx } from 'clsx'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
  footer?: React.ReactNode
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hoverable?: boolean
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      title,
      description,
      footer,
      padding = 'md',
      hoverable = false,
      children,
      ...props
    },
    ref
  ) => {
    const paddingStyles = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    }

    return (
      <div
        ref={ref}
        className={clsx(
          'rounded-xl border bg-white shadow-sm dark:bg-surface-900 dark:border-surface-800',
          hoverable && 'transition-shadow hover:shadow-md cursor-pointer',
          className
        )}
        {...props}
      >
        {(title || description) && (
          <div className={clsx('border-b dark:border-surface-800', paddingStyles[padding])}>
            {title && (
              <h3 className="text-lg font-semibold text-surface-900 dark:text-surface-100">
                {title}
              </h3>
            )}
            {description && (
              <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
                {description}
              </p>
            )}
          </div>
        )}
        <div className={paddingStyles[padding]}>{children}</div>
        {footer && (
          <div
            className={clsx(
              'border-t bg-surface-50 dark:bg-surface-800/50 dark:border-surface-800',
              paddingStyles[padding]
            )}
          >
            {footer}
          </div>
        )}
      </div>
    )
  }
)

Card.displayName = 'Card'

export default Card
