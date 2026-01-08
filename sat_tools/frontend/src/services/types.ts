// ============================================
// Common Types
// ============================================

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// ============================================
// Parameter Browser Types (SAT-001)
// ============================================

export interface ParameterValue {
  type: 'float' | 'int' | 'bool' | 'string' | 'float2' | 'float3' | 'float4' | 'enum'
  value: unknown
  defaultValue?: unknown
  min?: number
  max?: number
  step?: number
  options?: string[] // for enum type
}

export interface NodeParameter {
  id: string
  name: string
  label: string
  description?: string
  parameter: ParameterValue
}

export interface GraphNode {
  id: string
  name: string
  type: string
  category: string
  parameters: NodeParameter[]
}

export interface GraphInfo {
  id: string
  name: string
  description?: string
  category: string
  nodes: GraphNode[]
}

export interface ParameterFile {
  filename: string
  filepath: string
  fileType: 'sbs' | 'sbsar'
  extractedAt: string
  graphs: GraphInfo[]
  metadata: {
    version?: string
    author?: string
    description?: string
  }
}

// ============================================
// Thumbnail Manager Types (SAT-002)
// ============================================

export interface ThumbnailMetadata {
  sourceFile: string
  graphName: string
  generatedAt: string
  resolution: {
    width: number
    height: number
  }
  parameterHash: string
  tags: string[]
  customData?: Record<string, unknown>
}

export interface Thumbnail {
  id: string
  filename: string
  filepath: string
  url: string
  metadata: ThumbnailMetadata
  createdAt: string
}

// ============================================
// Asset Repository Types (SAT-003)
// ============================================

export interface AssetTexture {
  channel: string // e.g., 'baseColor', 'normal', 'roughness'
  filename: string
  url: string
  format: string
  resolution: {
    width: number
    height: number
  }
}

export interface Asset {
  id: string
  name: string
  description?: string
  sourceFile: string // SBS/SBSAR file name
  sourceFileUrl?: string // URL to download the source file
  fileType: 'sbs' | 'sbsar'
  textures: AssetTexture[] // Generated textures (can be empty if not baked yet)
  thumbnailUrl?: string
  tags: string[]
  createdAt: string
  updatedAt: string
  metadata?: Record<string, unknown>
  // Status tracking
  hasParameters?: boolean // Whether parameters have been extracted
  hasThumbnail?: boolean // Whether thumbnail has been generated
  hasBakedTextures?: boolean // Whether textures have been baked
}

export interface AssetUploadResult {
  assetId: string
  url: string
  textures: AssetTexture[]
}

// ============================================
// API Request/Response Types
// ============================================

export interface ExtractParametersRequest {
  filepath: string
}

export interface GenerateThumbnailRequest {
  filepath: string
  resolution?: number
  format?: 'png' | 'jpg'
  graphName?: string
}

export interface BakeTexturesRequest {
  filepath: string
  outputDir?: string
  resolution?: number
  format?: string
  channels?: string[]
}

export interface UploadAssetRequest {
  name: string
  description?: string
  tags?: string[]
  files: File[]
}

export interface SearchAssetsRequest {
  query?: string
  tags?: string[]
  page?: number
  pageSize?: number
  sortBy?: 'createdAt' | 'name'
  sortOrder?: 'asc' | 'desc'
}
