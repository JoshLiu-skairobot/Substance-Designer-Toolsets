import { useState, useEffect, useMemo } from 'react'
import { Image, RefreshCw, Info, Trash2, Download, Database, ExternalLink } from 'lucide-react'
import { Card, Button, SearchInput, Modal } from '@/components/ui'
import { useAssetStore } from '@/store'
import type { ThumbnailMetadata, Asset } from '@/services/types'
import { API_BASE, staticUrl } from '@/config/api'

interface ThumbnailItem {
  id: string
  assetId: string
  assetName: string
  filename: string
  url: string
  sourceFile: string
  fileType: string
  generatedAt: string
  resolution: { width: number; height: number }
}

const ThumbnailManager = () => {
  const { assets, updateAsset, loadAssets } = useAssetStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedThumbnail, setSelectedThumbnail] = useState<ThumbnailItem | null>(null)
  const [showMetadata, setShowMetadata] = useState(false)
  const [showAssetSelector, setShowAssetSelector] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [loading, setLoading] = useState(false)

  // Load assets on mount
  useEffect(() => {
    if (assets.length === 0) {
      handleRefresh()
    }
  }, [])

  const handleRefresh = async () => {
    setLoading(true)
    try {
      await loadAssets()
    } finally {
      setLoading(false)
    }
  }

  // Convert assets with thumbnails to ThumbnailItem format
  const thumbnails = useMemo<ThumbnailItem[]>(() => {
    return assets
      .filter((asset: Asset) => asset.hasThumbnail && asset.thumbnailUrl)
      .map((asset: Asset) => ({
        id: `thumb-${asset.id}`,
        assetId: asset.id,
        assetName: asset.name,
        filename: `${asset.name}_preview.png`,
        url: asset.thumbnailUrl!.startsWith('http') 
          ? asset.thumbnailUrl! 
          : staticUrl(asset.thumbnailUrl),
        sourceFile: asset.sourceFile,
        fileType: asset.fileType,
        generatedAt: asset.updatedAt,
        resolution: { width: 256, height: 256 }
      }))
  }, [assets])

  const filteredThumbnails = thumbnails.filter(
    (thumb) =>
      thumb.assetName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      thumb.sourceFile.toLowerCase().includes(searchQuery.toLowerCase()) ||
      thumb.fileType.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Filter assets that don't have thumbnails yet
  const assetsWithoutThumbnails = assets.filter((a: Asset) => !a.hasThumbnail)

  const handleGenerateFromAsset = async (asset: Asset) => {
    setGenerating(true)
    try {
      const response = await fetch(`${API_BASE}/api/assets/${asset.id}/generate-thumbnail`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution: 256 })
      })
      
      if (response.ok) {
        const result = await response.json()
        
        // Update asset in store
        updateAsset(asset.id, {
          hasThumbnail: true,
          thumbnailUrl: result.thumbnailUrl ? staticUrl(result.thumbnailUrl) : asset.thumbnailUrl
        })
        
        setShowAssetSelector(false)
        alert('缩略图生成成功！')
      } else {
        const error = await response.json()
        alert(`生成失败: ${error.error}`)
      }
    } catch (error) {
      console.error('Generate failed:', error)
      alert('生成失败，请确保后端服务正在运行')
    } finally {
      setGenerating(false)
    }
  }

  const handleBatchGenerate = async () => {
    if (assetsWithoutThumbnails.length === 0) {
      alert('没有需要生成缩略图的资产')
      return
    }
    
    setGenerating(true)
    let successCount = 0
    
    for (const asset of assetsWithoutThumbnails) {
      try {
        const response = await fetch(`${API_BASE}/api/assets/${asset.id}/generate-thumbnail`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ resolution: 256 })
        })
        
        if (response.ok) {
          const result = await response.json()
          updateAsset(asset.id, {
            hasThumbnail: true,
            thumbnailUrl: result.thumbnailUrl ? staticUrl(result.thumbnailUrl) : asset.thumbnailUrl
          })
          successCount++
        }
      } catch (error) {
        console.error(`Failed to generate thumbnail for ${asset.name}:`, error)
      }
    }
    
    setGenerating(false)
    alert(`成功生成 ${successCount} 个缩略图`)
  }

  const handleViewMetadata = (thumbnail: ThumbnailItem) => {
    setSelectedThumbnail(thumbnail)
    setShowMetadata(true)
  }

  const handleDownload = (thumbnail: ThumbnailItem) => {
    const link = document.createElement('a')
    link.href = thumbnail.url
    link.download = thumbnail.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-white">
            缩略图管理
          </h1>
          <p className="mt-1 text-surface-500 dark:text-surface-400">
            生成和管理Substance文件缩略图
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            icon={<RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />}
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
          <Button
            variant="secondary"
            icon={<Database className="h-4 w-4" />}
            onClick={() => setShowAssetSelector(true)}
          >
            从仓库选择
          </Button>
          {assetsWithoutThumbnails.length > 0 && (
            <Button
              variant="primary"
              icon={<RefreshCw className={`h-4 w-4 ${generating ? 'animate-spin' : ''}`} />}
              onClick={handleBatchGenerate}
              loading={generating}
            >
              批量生成 ({assetsWithoutThumbnails.length})
            </Button>
          )}
        </div>
      </div>

      {/* Info Banner */}
      {assets.length === 0 && (
        <Card className="bg-blue-50 dark:bg-blue-900/20">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900 dark:text-blue-100">
                没有可用的资产
              </h4>
              <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                请先在资产仓库中上传 SBS/SBSAR 文件，然后返回此页面生成缩略图。
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Search & Filter */}
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <SearchInput
            className="w-full sm:w-80"
            placeholder="搜索缩略图..."
            value={searchQuery}
            onChange={setSearchQuery}
          />
          <div className="flex items-center gap-4">
            <span className="text-sm text-surface-500">
              已生成: {thumbnails.length} / {assets.length}
            </span>
          </div>
        </div>
      </Card>

      {/* Thumbnail Grid */}
      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {filteredThumbnails.map((thumbnail) => (
          <Card
            key={thumbnail.id}
            padding="none"
            hoverable
            className="group overflow-hidden"
          >
            <div className="relative aspect-square bg-surface-100 dark:bg-surface-800">
              <img
                src={thumbnail.url}
                alt={thumbnail.assetName}
                className="h-full w-full object-cover"
              />
              <div className="absolute left-2 top-2">
                <span className="rounded bg-black/50 px-2 py-1 text-xs font-medium text-white">
                  {thumbnail.fileType.toUpperCase()}
                </span>
              </div>
              <div className="absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  onClick={() => handleViewMetadata(thumbnail)}
                  className="rounded-lg bg-white/20 p-2 text-white backdrop-blur hover:bg-white/30"
                  title="查看Metadata"
                >
                  <Info className="h-5 w-5" />
                </button>
                <button
                  onClick={() => handleDownload(thumbnail)}
                  className="rounded-lg bg-white/20 p-2 text-white backdrop-blur hover:bg-white/30"
                  title="下载"
                >
                  <Download className="h-5 w-5" />
                </button>
              </div>
            </div>
            <div className="p-3">
              <p className="truncate text-sm font-medium text-surface-900 dark:text-white">
                {thumbnail.assetName}
              </p>
              <p className="truncate text-xs text-surface-500">
                {thumbnail.sourceFile}
              </p>
              <p className="mt-1 text-xs text-surface-400">
                {thumbnail.resolution.width} × {thumbnail.resolution.height}
              </p>
            </div>
          </Card>
        ))}

        {filteredThumbnails.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center py-12">
            <Image className="h-16 w-16 text-surface-300" />
            <p className="mt-4 text-surface-500">暂无已生成的缩略图</p>
            {assets.length > 0 ? (
              <Button 
                className="mt-4" 
                variant="primary" 
                onClick={() => setShowAssetSelector(true)}
              >
                从仓库选择文件生成
              </Button>
            ) : (
              <p className="mt-2 text-sm text-surface-400">
                请先在资产仓库上传文件
              </p>
            )}
          </div>
        )}
      </div>

      {/* Metadata Modal */}
      <Modal
        isOpen={showMetadata}
        onClose={() => setShowMetadata(false)}
        title="缩略图详情"
        size="md"
      >
        {selectedThumbnail && (
          <ThumbnailDetail thumbnail={selectedThumbnail} />
        )}
      </Modal>

      {/* Asset Selector Modal */}
      <Modal
        isOpen={showAssetSelector}
        onClose={() => !generating && setShowAssetSelector(false)}
        title="选择资产生成缩略图"
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-sm text-surface-600 dark:text-surface-400">
            选择一个资产来生成缩略图。只显示尚未生成缩略图的资产。
          </p>
          
          {assets.length === 0 ? (
            <div className="py-8 text-center">
              <Database className="mx-auto h-12 w-12 text-surface-300" />
              <p className="mt-4 text-surface-500">
                资产仓库为空，请先上传 SBS/SBSAR 文件
              </p>
            </div>
          ) : assetsWithoutThumbnails.length === 0 ? (
            <div className="py-8 text-center">
              <Image className="mx-auto h-12 w-12 text-green-400" />
              <p className="mt-4 text-surface-500">
                所有资产都已生成缩略图！
              </p>
            </div>
          ) : (
            <div className="max-h-96 space-y-2 overflow-y-auto">
              {assetsWithoutThumbnails.map((asset: Asset) => (
                <div
                  key={asset.id}
                  className="flex items-center justify-between rounded-lg border p-3 hover:bg-surface-50 dark:border-surface-700 dark:hover:bg-surface-800"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-12 w-12 rounded bg-surface-200 dark:bg-surface-700 flex items-center justify-center">
                      <Image className="h-6 w-6 text-surface-400" />
                    </div>
                    <div>
                      <p className="font-medium text-surface-900 dark:text-white">
                        {asset.name}
                      </p>
                      <p className="text-xs text-surface-500">
                        {asset.sourceFile} • {asset.fileType.toUpperCase()}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleGenerateFromAsset(asset)}
                    loading={generating}
                  >
                    生成缩略图
                  </Button>
                </div>
              ))}
            </div>
          )}
          
          {generating && (
            <div className="flex items-center justify-center gap-2 py-4">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
              <span className="text-sm">正在生成缩略图...</span>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

// Thumbnail detail component
const ThumbnailDetail = ({ thumbnail }: { thumbnail: ThumbnailItem }) => {
  const items = [
    { label: '资产名称', value: thumbnail.assetName },
    { label: '源文件', value: thumbnail.sourceFile },
    { label: '文件类型', value: thumbnail.fileType.toUpperCase() },
    { label: '分辨率', value: `${thumbnail.resolution.width} × ${thumbnail.resolution.height}` },
    { label: '生成时间', value: new Date(thumbnail.generatedAt).toLocaleString() },
    { label: '资产ID', value: thumbnail.assetId },
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-center">
        <img
          src={thumbnail.url}
          alt={thumbnail.assetName}
          className="max-h-64 rounded-lg object-contain shadow-lg"
        />
      </div>
      <div className="divide-y rounded-lg border dark:divide-surface-800 dark:border-surface-800">
        {items.map((item) => (
          <div key={item.label} className="flex items-center justify-between px-4 py-3">
            <span className="text-sm text-surface-500 dark:text-surface-400">
              {item.label}
            </span>
            <span className="text-sm font-medium text-surface-900 dark:text-white">
              {item.value}
            </span>
          </div>
        ))}
      </div>
      <div className="flex justify-center">
        <a
          href={thumbnail.url}
          download={thumbnail.filename}
          className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
        >
          <Download className="h-4 w-4" />
          下载缩略图
        </a>
      </div>
    </div>
  )
}

export default ThumbnailManager
