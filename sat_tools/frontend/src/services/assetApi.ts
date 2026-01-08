import { apiGet, apiPost, apiDelete, apiUpload } from './api'
import type { 
  Asset, 
  AssetUploadResult, 
  PaginatedResponse, 
  SearchAssetsRequest,
  BakeTexturesRequest 
} from './types'

export const assetApi = {
  /**
   * Get list of all assets with pagination
   */
  getList: (params?: { page?: number; pageSize?: number }) => 
    apiGet<PaginatedResponse<Asset>>('/assets', params),

  /**
   * Get asset by ID
   */
  getById: (id: string) => 
    apiGet<Asset>(`/assets/${id}`),

  /**
   * Search assets
   */
  search: (params: SearchAssetsRequest) => 
    apiGet<PaginatedResponse<Asset>>('/assets/search', params as Record<string, unknown>),

  /**
   * Upload asset files
   */
  upload: (file: File, onProgress?: (percent: number) => void) => 
    apiUpload<AssetUploadResult>('/assets/upload', file, onProgress),

  /**
   * Bake textures and upload to repository
   */
  bakeAndUpload: (data: BakeTexturesRequest) => 
    apiPost<AssetUploadResult>('/assets/bake', data),

  /**
   * Update asset metadata
   */
  update: (id: string, data: Partial<Asset>) => 
    apiPost<Asset>(`/assets/${id}`, data),

  /**
   * Delete an asset
   */
  delete: (id: string) => 
    apiDelete<void>(`/assets/${id}`),

  /**
   * Get asset download URL
   */
  getDownloadUrl: (id: string, channel?: string) => 
    apiGet<{ url: string }>(`/assets/${id}/download`, { channel }),
}
