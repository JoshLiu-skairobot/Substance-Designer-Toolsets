import { useState, useEffect, useMemo } from 'react'
import { FileJson, FolderOpen, RefreshCw, File, Database, Info, Eye } from 'lucide-react'
import { Card, Button, SearchInput, Modal } from '@/components/ui'
import TreeView, { type TreeNode } from '@/components/ui/TreeView'
import { useAssetStore } from '@/store'
import type { ParameterFile, GraphNode, NodeParameter, Asset } from '@/services/types'
import { API_BASE } from '@/config/api'

const ParameterBrowser = () => {
  const { assets, loadAssets, updateAsset } = useAssetStore()
  const [files, setFiles] = useState<ParameterFile[]>([])
  const [selectedFile, setSelectedFile] = useState<ParameterFile | null>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showAssetSelector, setShowAssetSelector] = useState(false)
  const [extracting, setExtracting] = useState(false)
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

  // Assets with parameters already extracted
  const assetsWithParameters = useMemo(() => 
    assets.filter((a: Asset) => a.hasParameters), [assets])
  
  // Filter assets that don't have parameters yet
  const assetsWithoutParameters = useMemo(() => 
    assets.filter((a: Asset) => !a.hasParameters), [assets])

  // Convert parameter file to tree nodes
  const buildTreeNodes = (file: ParameterFile): TreeNode[] => {
    return file.graphs.map((graph) => ({
      id: graph.id,
      label: graph.name,
      icon: <FolderOpen className="h-4 w-4 text-yellow-500" />,
      children: graph.nodes.map((node) => ({
        id: node.id,
        label: `${node.name} (${node.type})`,
        icon: <FileJson className="h-4 w-4 text-blue-500" />,
        data: node,
      })),
    }))
  }

  const handleNodeSelect = (treeNode: TreeNode) => {
    if (!selectedFile) return

    for (const graph of selectedFile.graphs) {
      const node = graph.nodes.find((n) => n.id === treeNode.id)
      if (node) {
        setSelectedNode(node)
        break
      }
    }
  }

  const handleExtractFromAsset = async (asset: Asset) => {
    setExtracting(true)
    try {
      const response = await fetch(`${API_BASE}/api/assets/${asset.id}/extract-parameters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (response.ok) {
        const result = await response.json()
        
        if (result.success && result.parameters) {
          // Add to files list
          const newFile: ParameterFile = {
            filename: result.parameters.filename,
            filepath: result.parameters.filepath,
            fileType: result.parameters.fileType,
            extractedAt: result.parameters.extractedAt,
            graphs: result.parameters.graphs,
            metadata: result.parameters.metadata,
          }
          
          setFiles(prev => [newFile, ...prev])
          setSelectedFile(newFile)
          
          // Update asset in store
          updateAsset(asset.id, { hasParameters: true })
          
          setShowAssetSelector(false)
          alert('参数提取成功！')
        } else {
          alert(`提取失败: ${result.error || '未知错误'}`)
        }
      } else {
        const error = await response.json()
        alert(`提取失败: ${error.error}`)
      }
    } catch (error) {
      console.error('Extract failed:', error)
      alert('提取失败，请确保后端服务正在运行')
    } finally {
      setExtracting(false)
    }
  }

  const handleBatchExtract = async () => {
    if (assetsWithoutParameters.length === 0) {
      alert('没有需要提取参数的资产')
      return
    }
    
    setExtracting(true)
    let successCount = 0
    
    for (const asset of assetsWithoutParameters) {
      try {
        const response = await fetch(`${API_BASE}/api/assets/${asset.id}/extract-parameters`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
        
        if (response.ok) {
          const result = await response.json()
          
          if (result.success && result.parameters) {
            const newFile: ParameterFile = {
              filename: result.parameters.filename,
              filepath: result.parameters.filepath,
              fileType: result.parameters.fileType,
              extractedAt: result.parameters.extractedAt,
              graphs: result.parameters.graphs,
              metadata: result.parameters.metadata,
            }
            
            setFiles(prev => [newFile, ...prev])
            updateAsset(asset.id, { hasParameters: true })
            successCount++
          }
        }
      } catch (error) {
        console.error(`Failed to extract parameters for ${asset.name}:`, error)
      }
    }
    
    setExtracting(false)
    alert(`成功提取 ${successCount} 个文件的参数`)
  }

  // Handle viewing parameters from an asset that already has them
  const handleViewAssetParameters = async (asset: Asset) => {
    if (!asset.hasParameters) return
    
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/assets/${asset.id}/extract-parameters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (response.ok) {
        const result = await response.json()
        
        if (result.success && result.parameters) {
          const newFile: ParameterFile = {
            filename: result.parameters.filename,
            filepath: result.parameters.filepath,
            fileType: result.parameters.fileType,
            extractedAt: result.parameters.extractedAt,
            graphs: result.parameters.graphs,
            metadata: result.parameters.metadata,
          }
          
          // Check if file already exists in list
          const existingIndex = files.findIndex(f => f.filename === newFile.filename)
          if (existingIndex >= 0) {
            setFiles(prev => prev.map((f, i) => i === existingIndex ? newFile : f))
          } else {
            setFiles(prev => [newFile, ...prev])
          }
          setSelectedFile(newFile)
          setSelectedNode(null)
        }
      }
    } catch (error) {
      console.error('Failed to load parameters:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-white">
            参数浏览器
          </h1>
          <p className="mt-1 text-surface-500 dark:text-surface-400">
            浏览和管理Substance文件的参数
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
          {assetsWithoutParameters.length > 0 && (
            <Button
              variant="primary"
              icon={<RefreshCw className={`h-4 w-4 ${extracting ? 'animate-spin' : ''}`} />}
              onClick={handleBatchExtract}
              loading={extracting}
            >
              批量提取 ({assetsWithoutParameters.length})
            </Button>
          )}
        </div>
      </div>

      {/* Stats Banner */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div>
              <p className="text-2xl font-bold text-surface-900 dark:text-white">
                {assetsWithParameters.length}
              </p>
              <p className="text-sm text-surface-500">已提取参数</p>
            </div>
            <div className="h-8 w-px bg-surface-200 dark:bg-surface-700" />
            <div>
              <p className="text-2xl font-bold text-surface-900 dark:text-white">
                {assetsWithoutParameters.length}
              </p>
              <p className="text-sm text-surface-500">待提取</p>
            </div>
            <div className="h-8 w-px bg-surface-200 dark:bg-surface-700" />
            <div>
              <p className="text-2xl font-bold text-surface-900 dark:text-white">
                {files.length}
              </p>
              <p className="text-sm text-surface-500">已加载</p>
            </div>
          </div>
        </div>
      </Card>

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
                请先在资产仓库中上传 SBS/SBSAR 文件，然后返回此页面提取参数。
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Quick access to assets with parameters */}
      {assetsWithParameters.length > 0 && files.length === 0 && (
        <Card>
          <h3 className="mb-3 font-medium text-surface-900 dark:text-white">
            已提取参数的资产
          </h3>
          <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {assetsWithParameters.slice(0, 8).map((asset: Asset) => (
              <button
                key={asset.id}
                onClick={() => handleViewAssetParameters(asset)}
                className="flex items-center gap-3 rounded-lg border p-3 text-left hover:bg-surface-50 dark:border-surface-700 dark:hover:bg-surface-800"
              >
                <img
                  src={asset.thumbnailUrl}
                  alt={asset.name}
                  className="h-10 w-10 rounded object-cover"
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-surface-900 dark:text-white">
                    {asset.name}
                  </p>
                  <p className="text-xs text-surface-500">{asset.fileType.toUpperCase()}</p>
                </div>
                <Eye className="h-4 w-4 text-surface-400" />
              </button>
            ))}
          </div>
          {assetsWithParameters.length > 8 && (
            <p className="mt-2 text-center text-sm text-surface-500">
              还有 {assetsWithParameters.length - 8} 个资产...
            </p>
          )}
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-12">
        {/* File List */}
        <Card className="lg:col-span-3">
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-surface-900 dark:text-white">
              已提取的文件 ({files.length})
            </h2>
            {files.length === 0 ? (
              <div className="py-8 text-center">
                <FileJson className="mx-auto h-12 w-12 text-surface-300" />
                <p className="mt-2 text-sm text-surface-500">
                  暂无提取的参数文件
                </p>
                {assets.length > 0 && (
                  <Button 
                    className="mt-4" 
                    size="sm" 
                    variant="secondary"
                    onClick={() => setShowAssetSelector(true)}
                  >
                    选择资产提取
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-1">
                {files.map((file) => (
                  <button
                    key={file.filename}
                    onClick={() => {
                      setSelectedFile(file)
                      setSelectedNode(null)
                    }}
                    className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors ${
                      selectedFile?.filename === file.filename
                        ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                        : 'hover:bg-surface-100 dark:hover:bg-surface-800'
                    }`}
                  >
                    <File className="h-4 w-4 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{file.filename}</p>
                      <p className="text-xs text-surface-500">
                        {file.graphs.length} graph(s)
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Graph Tree */}
        <Card className="lg:col-span-4">
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-surface-900 dark:text-white">
              Graph 结构
            </h2>
            <SearchInput
              placeholder="搜索节点..."
              value={searchQuery}
              onChange={setSearchQuery}
            />
            {selectedFile ? (
              <TreeView
                nodes={buildTreeNodes(selectedFile)}
                onSelect={handleNodeSelect}
                defaultExpandAll
              />
            ) : (
              <p className="py-8 text-center text-sm text-surface-500">
                请选择一个文件
              </p>
            )}
          </div>
        </Card>

        {/* Parameter Details */}
        <Card className="lg:col-span-5">
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-surface-900 dark:text-white">
              参数详情
            </h2>
            {selectedNode ? (
              <div className="space-y-4">
                <div className="rounded-lg bg-surface-50 p-4 dark:bg-surface-900">
                  <h3 className="font-semibold text-surface-900 dark:text-white">
                    {selectedNode.name}
                  </h3>
                  <p className="text-sm text-surface-500">{selectedNode.type}</p>
                  <p className="mt-1 text-xs text-surface-400">
                    分类: {selectedNode.category}
                  </p>
                </div>

                <div className="space-y-3">
                  {selectedNode.parameters.map((param) => (
                    <ParameterItem key={param.id} parameter={param} />
                  ))}
                </div>
              </div>
            ) : (
              <p className="py-8 text-center text-sm text-surface-500">
                请选择一个节点查看参数
              </p>
            )}
          </div>
        </Card>
      </div>

      {/* Asset Selector Modal */}
      <Modal
        isOpen={showAssetSelector}
        onClose={() => !extracting && setShowAssetSelector(false)}
        title="选择资产提取参数"
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-sm text-surface-600 dark:text-surface-400">
            选择一个资产来提取参数。这将分析 SBS/SBSAR 文件并提取所有可配置的输入参数。
          </p>
          
          {assets.length === 0 ? (
            <div className="py-8 text-center">
              <Database className="mx-auto h-12 w-12 text-surface-300" />
              <p className="mt-4 text-surface-500">
                资产仓库为空，请先上传 SBS/SBSAR 文件
              </p>
            </div>
          ) : assetsWithoutParameters.length === 0 ? (
            <div className="py-8 text-center">
              <FileJson className="mx-auto h-12 w-12 text-green-400" />
              <p className="mt-4 text-surface-500">
                所有资产都已提取参数！
              </p>
            </div>
          ) : (
            <div className="max-h-96 space-y-2 overflow-y-auto">
              {assetsWithoutParameters.map((asset: Asset) => (
                <div
                  key={asset.id}
                  className="flex items-center justify-between rounded-lg border p-3 hover:bg-surface-50 dark:border-surface-700 dark:hover:bg-surface-800"
                >
                  <div className="flex items-center gap-3">
                    <img
                      src={asset.thumbnailUrl}
                      alt={asset.name}
                      className="h-12 w-12 rounded object-cover"
                    />
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
                    onClick={() => handleExtractFromAsset(asset)}
                    loading={extracting}
                  >
                    提取参数
                  </Button>
                </div>
              ))}
            </div>
          )}
          
          {extracting && (
            <div className="flex items-center justify-center gap-2 py-4">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
              <span className="text-sm">正在提取参数...</span>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

// Parameter item component
const ParameterItem = ({ parameter }: { parameter: NodeParameter }) => {
  const renderValue = () => {
    const { value } = parameter.parameter

    if (Array.isArray(value)) {
      return value.join(', ')
    }

    if (typeof value === 'boolean') {
      return value ? 'True' : 'False'
    }

    if (value === null || value === undefined) {
      return '(未设置)'
    }

    return String(value)
  }

  return (
    <div className="rounded-lg border border-surface-200 p-3 dark:border-surface-800">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-medium text-surface-900 dark:text-white">
            {parameter.label || parameter.name}
          </p>
          <p className="text-xs text-surface-500">{parameter.name}</p>
        </div>
        <span className="rounded bg-surface-100 px-2 py-1 text-xs font-mono text-surface-600 dark:bg-surface-800 dark:text-surface-400">
          {parameter.parameter.type}
        </span>
      </div>

      <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-surface-500">当前值:</span>
          <p className="font-medium text-surface-900 dark:text-white">
            {renderValue()}
          </p>
        </div>
        {parameter.parameter.defaultValue !== undefined && (
          <div>
            <span className="text-surface-500">默认值:</span>
            <p className="font-medium text-surface-900 dark:text-white">
              {Array.isArray(parameter.parameter.defaultValue)
                ? parameter.parameter.defaultValue.join(', ')
                : String(parameter.parameter.defaultValue ?? '(无)')}
            </p>
          </div>
        )}
      </div>

      {'min' in parameter.parameter && 'max' in parameter.parameter && (
        <div className="mt-2 text-xs text-surface-500">
          范围: {parameter.parameter.min} - {parameter.parameter.max}
        </div>
      )}
    </div>
  )
}

export default ParameterBrowser
