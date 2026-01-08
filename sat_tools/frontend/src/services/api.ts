import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error: AxiosError<{ message?: string }>) => {
    const message = error.response?.data?.message || error.message || '请求失败'
    
    // Handle specific error codes
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login if needed
      localStorage.removeItem('token')
    }
    
    console.error('[API Error]', message)
    return Promise.reject(new Error(message))
  }
)

export default api

// Helper functions for common HTTP methods
export const apiGet = <T>(url: string, params?: Record<string, unknown>) =>
  api.get<unknown, T>(url, { params })

export const apiPost = <T>(url: string, data?: unknown) =>
  api.post<unknown, T>(url, data)

export const apiPut = <T>(url: string, data?: unknown) =>
  api.put<unknown, T>(url, data)

export const apiDelete = <T>(url: string) =>
  api.delete<unknown, T>(url)

export const apiUpload = <T>(url: string, file: File, onProgress?: (percent: number) => void) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return api.post<unknown, T>(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      }
    },
  })
}
