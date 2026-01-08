import { useState, ReactNode } from 'react'
import { clsx } from 'clsx'
import { ChevronRight, ChevronDown, Folder, File } from 'lucide-react'

export interface TreeNode {
  id: string
  label: string
  icon?: ReactNode
  children?: TreeNode[]
  data?: unknown
}

export interface TreeViewProps {
  nodes: TreeNode[]
  onSelect?: (node: TreeNode) => void
  selectedId?: string
  expandedIds?: string[]
  onExpandChange?: (ids: string[]) => void
  className?: string
  defaultExpandAll?: boolean
}

const TreeView = ({
  nodes,
  onSelect,
  selectedId,
  expandedIds: controlledExpandedIds,
  onExpandChange,
  className,
  defaultExpandAll = false,
}: TreeViewProps) => {
  const [internalExpandedIds, setInternalExpandedIds] = useState<string[]>(
    defaultExpandAll ? getAllNodeIds(nodes) : []
  )

  const expandedIds = controlledExpandedIds ?? internalExpandedIds

  const toggleExpand = (id: string) => {
    const newIds = expandedIds.includes(id)
      ? expandedIds.filter((i) => i !== id)
      : [...expandedIds, id]

    if (onExpandChange) {
      onExpandChange(newIds)
    } else {
      setInternalExpandedIds(newIds)
    }
  }

  return (
    <div className={clsx('text-sm', className)}>
      {nodes.map((node) => (
        <TreeNodeItem
          key={node.id}
          node={node}
          level={0}
          expandedIds={expandedIds}
          selectedId={selectedId}
          onToggle={toggleExpand}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}

interface TreeNodeItemProps {
  node: TreeNode
  level: number
  expandedIds: string[]
  selectedId?: string
  onToggle: (id: string) => void
  onSelect?: (node: TreeNode) => void
}

const TreeNodeItem = ({
  node,
  level,
  expandedIds,
  selectedId,
  onToggle,
  onSelect,
}: TreeNodeItemProps) => {
  const hasChildren = node.children && node.children.length > 0
  const isExpanded = expandedIds.includes(node.id)
  const isSelected = selectedId === node.id

  const handleClick = () => {
    if (hasChildren) {
      onToggle(node.id)
    }
    onSelect?.(node)
  }

  const defaultIcon = hasChildren ? (
    <Folder className="h-4 w-4 text-primary-500" />
  ) : (
    <File className="h-4 w-4 text-surface-400" />
  )

  return (
    <div>
      <div
        onClick={handleClick}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        className={clsx(
          'flex cursor-pointer items-center gap-1 rounded-md px-2 py-1.5 hover:bg-surface-100 dark:hover:bg-surface-800',
          isSelected && 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
        )}
      >
        <span className="flex h-4 w-4 items-center justify-center">
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown className="h-4 w-4 text-surface-400" />
            ) : (
              <ChevronRight className="h-4 w-4 text-surface-400" />
            )
          ) : null}
        </span>
        <span className="flex items-center">{node.icon || defaultIcon}</span>
        <span className="truncate">{node.label}</span>
      </div>
      {hasChildren && isExpanded && (
        <div>
          {node.children!.map((child) => (
            <TreeNodeItem
              key={child.id}
              node={child}
              level={level + 1}
              expandedIds={expandedIds}
              selectedId={selectedId}
              onToggle={onToggle}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Helper to get all node IDs for defaultExpandAll
function getAllNodeIds(nodes: TreeNode[]): string[] {
  const ids: string[] = []
  const traverse = (nodes: TreeNode[]) => {
    for (const node of nodes) {
      ids.push(node.id)
      if (node.children) {
        traverse(node.children)
      }
    }
  }
  traverse(nodes)
  return ids
}

export default TreeView
