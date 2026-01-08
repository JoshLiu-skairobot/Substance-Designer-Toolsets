import { apiGet, apiPost } from './api'
import type { ParameterFile, ExtractParametersRequest } from './types'

export const parameterApi = {
  /**
   * Get list of all extracted parameter files
   */
  getList: () => 
    apiGet<ParameterFile[]>('/parameters'),

  /**
   * Get parameter file by filename
   */
  getByFilename: (filename: string) => 
    apiGet<ParameterFile>(`/parameters/${encodeURIComponent(filename)}`),

  /**
   * Extract parameters from an SBS/SBSAR file
   */
  extract: (data: ExtractParametersRequest) => 
    apiPost<ParameterFile>('/parameters/extract', data),

  /**
   * Search parameters across all files
   */
  search: (query: string) => 
    apiGet<ParameterFile[]>('/parameters/search', { query }),

  /**
   * Delete a parameter file
   */
  delete: (filename: string) => 
    apiGet<void>(`/parameters/${encodeURIComponent(filename)}`),
}
