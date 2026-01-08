import { useState, useEffect } from 'react'
import {
  Database,
  Upload,
  Grid,
  List,
  Download,
  Trash2,
  Copy,
  Check,
  Image,
  RefreshCw,
  CheckSquare,
  Square,
  FileJson,
} from 'lucide-react'
import { Card, Button, SearchInput, Table, Modal, FileUpload } from '@/components/ui'
import type { Column } from '@/components/ui'
import type { Asset } from '@/services/types'
import { useAssetStore } from '@/store'
import { API_BASE, staticUrl } from '@/config/api'

const AssetRepository = () => {
  const { 
    assets, 
    loadAssets, 
    addAsset, 
    updateAsset, 
    removeAsset,
    removeAssets,
    isLoading,
    selectedAssetIds,
    toggleSelectAsset,
    selectAllAssets,
    clearSelection,
  } = useAssetStore()
  
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)
  const [showDetail, setShowDetail] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [isSelectMode, setIsSelectMode] = useState(false)

  // Load assets from API on mount
  useEffect(() => {
    loadAssets()
  }, [])

  const filteredAssets = assets.filter(
    (asset: Asset) =>
      asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.sourceFile.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.tags.some((tag: string) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const handleViewDetail = (asset: Asset) => {
    if (isSelectMode) {
      toggleSelectAsset(asset.id)
      return
    }
    setSelectedAsset(asset)
    setShowDetail(true)
  }

  const handleDelete = async (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation()
    if (!confirm('确定要删除这个资产吗？')) return
    
    try {
      const response = await fetch(`${API_BASE}/api/assets/${id}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        removeAsset(id)
      }
    } catch (error) {
      console.error('Failed to delete asset:', error)
    }
  }

  const handleBatchDelete = async () => {
    const selectedIds = Array.from(selectedAssetIds)
    if (selectedIds.length === 0) return
    
    if (!confirm(`确定要删除选中的 ${selectedIds.length} 个资产吗？`)) return
    
    try {
      for (const id of selectedIds) {
        await fetch(`${API_BASE}/api/assets/${id}`, { method: 'DELETE' })
      }
      removeAssets(selectedIds)
      setIsSelectMode(false)
    } catch (error) {
      console.error('Failed to delete assets:', error)
    }
  }

  const handleCopyId = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation()
    navigator.clipboard.writeText(id)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handleUploadFiles = async (files: File[]) => {
    if (files.length === 0) return

    setUploading(true)
    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('name', file.name.replace(/\.(sbs|sbsar)$/i, ''))
        formData.append('tags', JSON.stringify(['uploaded', 'new']))
        
        const response = await fetch(`${API_BASE}/api/assets/upload`, {
          method: 'POST',
          body: formData
        })
        
        if (response.ok) {
          const result = await response.json()
          const newAsset: Asset = {
            id: result.id,
            name: result.name,
            description: '',
            sourceFile: result.sourceFile,
            sourceFileUrl: result.sourceFileUrl ? staticUrl(result.sourceFileUrl) : undefined,
            fileType: result.fileType || 'sbs',
            textures: [],
            thumbnailUrl: result.thumbnailUrl 
              ? staticUrl(result.thumbnailUrl)
              : `https://via.placeholder.com/128/6366f1/ffffff?text=${(result.fileType || 'sbs').toUpperCase()}`,
            tags: result.tags || ['uploaded', 'new', result.fileType || 'sbs'],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            hasParameters: result.hasParameters || false,
            hasThumbnail: result.hasThumbnail || false,
            hasBakedTextures: result.hasBakedTextures || false,
            metadata: result.metadata || {},
          }
          addAsset(newAsset)
          
          // Check for auto-process errors
          const autoProcess = result.autoProcess || {}
          const errors: string[] = []
          
          if (autoProcess.parameters?.error) {
            errors.push(`参数提取失败:\n${autoProcess.parameters.error}`)
          }
          if (autoProcess.thumbnail?.error) {
            errors.push(`缩略图生成失败:\n${autoProcess.thumbnail.error}`)
          }
          
          if (errors.length > 0) {
            alert(`文件 ${file.name} 上传成功，但自动处理遇到问题:\n\n${errors.join('\n\n')}`)
          }
        } else {
          const errorData = await response.json()
          alert(`上传失败: ${errorData.error || '未知错误'}`)
        }
      }
      
      setShowUpload(false)
      // Reload to get complete data including auto-processed results
      await loadAssets()
      alert(`上传完成！${files.length} 个文件已处理。\n请检查资产卡片上的状态标签确认处理结果。`)
    } catch (error) {
      console.error('Upload failed:', error)
      alert('上传失败，请确保后端服务正在运行')
    } finally {
      setUploading(false)
    }
  }

  const handleGenerateThumbnail = async (asset: Asset) => {
    try {
      const response = await fetch(`${API_BASE}/api/assets/${asset.id}/generate-thumbnail`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution: 256 })
      })
      
      if (response.ok) {
        const result = await response.json()
        updateAsset(asset.id, {
          thumbnailUrl: result.thumbnailUrl ? staticUrl(result.thumbnailUrl) : asset.thumbnailUrl,
          hasThumbnail: true
        })
        alert('缩略图生成成功！')
        loadAssets()
      } else {
        const error = await response.json()
        alert(`生成失败:\n\n${error.error}`)
      }
    } catch (error) {
      console.error('Generate thumbnail failed:', error)
      alert('生成失败，请检查后端服务')
    }
  }

  const handleExtractParameters = async (asset: Asset) => {
    try {
      const response = await fetch(`${API_BASE}/api/assets/${asset.id}/extract-parameters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        updateAsset(asset.id, { hasParameters: true })
        alert('参数提取成功！')
        loadAssets()
      } else {
        const error = await response.json()
        alert(`提取失败:\n\n${error.error}`)
      }
    } catch (error) {
      console.error('Extract parameters failed:', error)
      alert('提取失败，请检查后端服务')
    }
  }

  const columns: Column<Asset>[] = [
    {
      key: 'thumbnail',
      header: '预览',
      width: '80px',
      render: (_value, row) => (
        <img
          src={row.thumbnailUrl}
          alt={row.name}
          className="h-12 w-12 rounded object-cover cursor-pointer"
          onClick={() => handleViewDetail(row)}
        />
      ),
    },
    { key: 'name', header: '名称' },
    { key: 'sourceFile', header: '源文件' },
    {
      key: 'fileType',
      header: '类型',
      width: '80px',
      render: (_value, row) => (
        <span className="rounded bg-primary-100 px-2 py-1 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
          {row.fileType.toUpperCase()}
        </span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      width: '150px',
      render: (_value, row) => (
        <div className="flex gap-1">
          {row.hasThumbnail && (
            <span className="rounded px-1.5 py-0.5 text-xs bg-green-100 text-green-700">
              缩略图
            </span>
          )}
          {row.hasParameters && (
            <span className="rounded px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700">
              参数
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'createdAt',
      header: '创建时间',
      render: (_value, row) => new Date(row.createdAt).toLocaleDateString(),
    },
    {
      key: 'actions',
      header: '操作',
      width: '100px',
      render: (_value, row) => (
        <div className="flex gap-1">
          <button
            onClick={(e) => handleCopyId(row.id, e)}
            className="rounded p-1.5 hover:bg-surface-100 dark:hover:bg-surface-800"
            title="复制ID"
          >
            {copiedId === row.id ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={(e) => handleDelete(row.id, e)}
            className="rounded p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
            title="删除"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-white">
            资产仓库
          </h1>
          <p className="mt-1 text-surface-500 dark:text-surface-400">
            管理Substance源文件和烘焙的贴图
          </p>
        </div>
        <div className="flex gap-2">
          {isSelectMode ? (
            <>
              <Button
                variant="secondary"
                onClick={() => { setIsSelectMode(false); clearSelection() }}
              >
                取消
              </Button>
              <Button
                variant="secondary"
                onClick={selectAllAssets}
              >
                全选 ({assets.length})
              </Button>
              <Button
                variant="primary"
                icon={<Trash2 className="h-4 w-4" />}
                onClick={handleBatchDelete}
                disabled={selectedAssetIds.size === 0}
              >
                删除 ({selectedAssetIds.size})
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="secondary"
                icon={<CheckSquare className="h-4 w-4" />}
                onClick={() => setIsSelectMode(true)}
              >
                多选
              </Button>
              <Button
                variant="secondary"
                icon={<RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />}
                onClick={loadAssets}
                loading={isLoading}
              >
                刷新
              </Button>
              <Button
                variant="primary"
                icon={<Upload className="h-4 w-4" />}
                onClick={() => setShowUpload(true)}
              >
                上传资产
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Search & Filter */}
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <SearchInput
            className="w-full sm:w-80"
            placeholder="搜索资产..."
            value={searchQuery}
            onChange={setSearchQuery}
          />
          <div className="flex items-center gap-4">
            <p className="text-sm text-surface-500">
              共 {filteredAssets.length} 个资产
            </p>
            <div className="flex rounded-lg border dark:border-surface-700">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-surface-100 dark:bg-surface-800' : ''}`}
              >
                <Grid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 ${viewMode === 'list' ? 'bg-surface-100 dark:bg-surface-800' : ''}`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Asset List/Grid */}
      {viewMode === 'list' ? (
        <Table
          columns={columns as unknown as Column<Record<string, unknown>>[]}
          data={filteredAssets as unknown as Record<string, unknown>[]}
          onRowClick={(row) => handleViewDetail(row as unknown as Asset)}
          emptyMessage="暂无资产，请上传 SBS/SBSAR 文件"
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {filteredAssets.map((asset: Asset) => (
            <Card
              key={asset.id}
              padding="none"
              hoverable
              className={`group overflow-hidden cursor-pointer relative ${
                selectedAssetIds.has(asset.id) ? 'ring-2 ring-primary-500' : ''
              }`}
              onClick={() => handleViewDetail(asset)}
            >
              {/* Selection checkbox */}
              {isSelectMode && (
                <div 
                  className="absolute left-2 top-2 z-10"
                  onClick={(e) => { e.stopPropagation(); toggleSelectAsset(asset.id) }}
                >
                  {selectedAssetIds.has(asset.id) ? (
                    <CheckSquare className="h-6 w-6 text-primary-500" />
                  ) : (
                    <Square className="h-6 w-6 text-white drop-shadow" />
                  )}
                </div>
              )}
              
              <div className="relative aspect-square bg-surface-100 dark:bg-surface-800">
                <img
                  src={asset.thumbnailUrl}
                  alt={asset.name}
                  className="h-full w-full object-cover"
                />
                {!isSelectMode && (
                  <div className="absolute right-2 top-2">
                    <span className="rounded bg-black/50 px-2 py-1 text-xs font-medium text-white">
                      {asset.fileType.toUpperCase()}
                    </span>
                  </div>
                )}
              </div>
              
              <div className="p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="truncate font-medium text-surface-900 dark:text-white">
                      {asset.name}
                    </p>
                    <p className="truncate text-xs text-surface-500">{asset.sourceFile}</p>
                  </div>
                  {/* Delete button in bottom right */}
                  {!isSelectMode && (
                    <button
                      onClick={(e) => handleDelete(asset.id, e)}
                      className="flex-shrink-0 rounded p-1.5 text-surface-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                      title="删除"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
                <div className="mt-2 flex gap-1">
                  {asset.hasThumbnail && (
                    <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-400">
                      缩略图
                    </span>
                  )}
                  {asset.hasParameters && (
                    <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                      参数
                    </span>
                  )}
                </div>
              </div>
            </Card>
          ))}

          {filteredAssets.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center py-12">
              <Database className="h-16 w-16 text-surface-300" />
              <p className="mt-4 text-surface-500">暂无资产</p>
              <Button
                className="mt-4"
                variant="primary"
                onClick={() => setShowUpload(true)}
              >
                上传第一个资产
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Detail Modal */}
      <Modal
        isOpen={showDetail}
        onClose={() => setShowDetail(false)}
        title="资产详情"
        size="lg"
      >
        {selectedAsset && (
          <AssetDetail 
            asset={selectedAsset} 
            onGenerateThumbnail={() => handleGenerateThumbnail(selectedAsset)}
            onExtractParameters={() => handleExtractParameters(selectedAsset)}
          />
        )}
      </Modal>

      {/* Upload Modal */}
      <Modal
        isOpen={showUpload}
        onClose={() => !uploading && setShowUpload(false)}
        title="上传资产"
        size="lg"
      >
        <div className="space-y-4">
          <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
            <h4 className="font-medium text-blue-900 dark:text-blue-100">上传 Substance 源文件</h4>
            <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
              上传 SBS 或 SBSAR 文件到资产仓库。上传后系统将自动：
            </p>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-blue-700 dark:text-blue-300">
              <li>提取所有可配置参数</li>
              <li>生成预览缩略图</li>
              <li>建立资产元数据索引</li>
            </ul>
          </div>
          <FileUpload
            accept=".sbs,.sbsar"
            multiple
            maxSize={500}
            onFilesSelected={handleUploadFiles}
            buttonText="选择 SBS/SBSAR 文件"
            buttonVariant="primary"
          />
          {uploading && (
            <div className="flex items-center justify-center gap-2 py-4">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
              <span className="text-sm">上传中，正在自动处理...</span>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

// Asset detail component
interface AssetDetailProps {
  asset: Asset
  onGenerateThumbnail: () => void
  onExtractParameters: () => void
}

const AssetDetail = ({ asset, onGenerateThumbnail, onExtractParameters }: AssetDetailProps) => {
  return (
    <div className="space-y-6">
      <div className="flex gap-4">
        <img
          src={asset.thumbnailUrl}
          alt={asset.name}
          className="h-24 w-24 rounded-lg object-cover"
        />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-surface-900 dark:text-white">
            {asset.name}
          </h3>
          <p className="text-sm text-surface-500">{asset.description}</p>
          <div className="mt-2 flex items-center gap-2">
            <code className="rounded bg-surface-100 px-2 py-1 text-xs dark:bg-surface-800">
              {asset.id}
            </code>
            <span className="rounded bg-primary-100 px-2 py-1 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
              {asset.fileType.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      <div>
        <h4 className="mb-2 font-medium text-surface-900 dark:text-white">源文件</h4>
        <div className="rounded-lg border p-3 dark:border-surface-800">
          <div className="flex items-center justify-between">
            <span className="text-sm font-mono text-surface-700 dark:text-surface-300">
              {asset.sourceFile}
            </span>
            {asset.sourceFileUrl && (
              <a
                href={asset.sourceFileUrl}
                download={asset.sourceFile}
                className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
              >
                下载
              </a>
            )}
          </div>
        </div>
      </div>

      <div>
        <h4 className="mb-2 font-medium text-surface-900 dark:text-white">处理状态</h4>
        <div className="grid grid-cols-3 gap-3">
          <div className={`rounded-lg border p-3 text-center ${asset.hasParameters ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : 'border-surface-300 dark:border-surface-700'}`}>
            <div className="text-xs text-surface-500">参数提取</div>
            <div className="mt-1 text-sm font-medium">
              {asset.hasParameters ? '✓ 已完成' : '未完成'}
            </div>
            {!asset.hasParameters && (
              <Button 
                size="sm" 
                variant="secondary" 
                className="mt-2"
                onClick={onExtractParameters}
              >
                提取
              </Button>
            )}
          </div>
          <div className={`rounded-lg border p-3 text-center ${asset.hasThumbnail ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : 'border-surface-300 dark:border-surface-700'}`}>
            <div className="text-xs text-surface-500">缩略图</div>
            <div className="mt-1 text-sm font-medium">
              {asset.hasThumbnail ? '✓ 已生成' : '未生成'}
            </div>
            {!asset.hasThumbnail && (
              <Button 
                size="sm" 
                variant="secondary" 
                className="mt-2"
                onClick={onGenerateThumbnail}
              >
                生成
              </Button>
            )}
          </div>
          <div className={`rounded-lg border p-3 text-center ${asset.hasBakedTextures ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : 'border-surface-300 dark:border-surface-700'}`}>
            <div className="text-xs text-surface-500">贴图烘焙</div>
            <div className="mt-1 text-sm font-medium">
              {asset.hasBakedTextures ? '✓ 已烘焙' : '未烘焙'}
            </div>
          </div>
        </div>
      </div>

      {/* Parameter metadata preview */}
      {asset.hasParameters && asset.metadata?.parameters && (
        <div>
          <h4 className="mb-2 font-medium text-surface-900 dark:text-white">参数概览</h4>
          <div className="rounded-lg border p-3 dark:border-surface-800 max-h-48 overflow-y-auto">
            <pre className="text-xs text-surface-600 dark:text-surface-400">
              {JSON.stringify(asset.metadata.parameters, null, 2).slice(0, 500)}
              {JSON.stringify(asset.metadata.parameters).length > 500 && '...'}
            </pre>
          </div>
        </div>
      )}

      <div>
        <h4 className="mb-2 font-medium text-surface-900 dark:text-white">
          烘焙的贴图 {asset.textures.length > 0 && `(${asset.textures.length})`}
        </h4>
        {asset.textures.length > 0 ? (
          <div className="divide-y rounded-lg border dark:divide-surface-800 dark:border-surface-800">
            {asset.textures.map((texture) => (
              <div
                key={texture.channel}
                className="flex items-center justify-between px-4 py-3"
              >
                <div>
                  <p className="font-medium text-surface-900 dark:text-white capitalize">
                    {texture.channel}
                  </p>
                  <p className="text-xs text-surface-500">
                    {texture.filename} • {texture.resolution.width}×{texture.resolution.height}
                  </p>
                </div>
                <Button variant="ghost" size="sm" icon={<Download className="h-4 w-4" />}>
                  下载
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed p-8 text-center dark:border-surface-700">
            <p className="text-sm text-surface-500">
              尚未烘焙贴图。上传源文件后，可以在缩略图管理器中生成预览，或烘焙完整贴图。
            </p>
          </div>
        )}
      </div>

      <div>
        <h4 className="mb-2 font-medium text-surface-900 dark:text-white">标签</h4>
        <div className="flex flex-wrap gap-2">
          {asset.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-primary-100 px-3 py-1 text-sm text-primary-700 dark:bg-primary-900/30 dark:text-primary-400"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="text-xs text-surface-500">
        <p>创建时间: {new Date(asset.createdAt).toLocaleString()}</p>
        <p>更新时间: {new Date(asset.updatedAt).toLocaleString()}</p>
      </div>
    </div>
  )
}

export default AssetRepository
