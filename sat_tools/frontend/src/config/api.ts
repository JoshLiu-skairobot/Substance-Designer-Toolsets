/**
 * API Configuration
 * 
 * Uses relative paths so that requests go through Vite proxy in development
 * and work correctly in production when served from the same origin.
 * 
 * For LAN access, the Vite dev server proxies /api and /static to the backend.
 */

// In development, use empty string to leverage Vite proxy
// In production, this could be configured via environment variable
export const API_BASE = ''

// Helper to construct API URLs
export const apiUrl = (path: string): string => {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${normalizedPath}`
}

// Helper to construct static asset URLs (e.g., thumbnails)
export const staticUrl = (path: string): string => {
  if (!path) return ''
  // If already a full URL or data URL, return as-is
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {
    return path
  }
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${normalizedPath}`
}
