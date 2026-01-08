import { apiGet, apiPost, apiDelete } from './api'
import type { Thumbnail, ThumbnailMetadata, GenerateThumbnailRequest } from './types'

export const thumbnailApi = {
  /**
   * Get list of all thumbnails
   */
  getList: () => 
    apiGet<Thumbnail[]>('/thumbnails'),

  /**
   * Get thumbnail by ID
   */
  getById: (id: string) => 
    apiGet<Thumbnail>(`/thumbnails/${id}`),

  /**
   * Get thumbnail metadata
   */
  getMetadata: (id: string) => 
    apiGet<ThumbnailMetadata>(`/thumbnails/${id}/metadata`),

  /**
   * Generate thumbnail for an SBS/SBSAR file
   */
  generate: (data: GenerateThumbnailRequest) => 
    apiPost<Thumbnail>('/thumbnails/generate', data),

  /**
   * Batch generate thumbnails for a directory
   */
  batchGenerate: (directory: string, options?: { resolution?: number; format?: string }) => 
    apiPost<Thumbnail[]>('/thumbnails/batch', { directory, ...options }),

  /**
   * Update thumbnail metadata
   */
  updateMetadata: (id: string, metadata: Partial<ThumbnailMetadata>) => 
    apiPost<Thumbnail>(`/thumbnails/${id}/metadata`, metadata),

  /**
   * Delete a thumbnail
   */
  delete: (id: string) => 
    apiDelete<void>(`/thumbnails/${id}`),
}
