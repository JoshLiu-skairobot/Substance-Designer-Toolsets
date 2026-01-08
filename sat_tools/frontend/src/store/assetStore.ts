/**
 * Asset Store
 * 
 * Shared state for assets across all views.
 * This enables the thumbnail manager and parameter browser
 * to access assets from the repository.
 */

import { create } from 'zustand'
import type { Asset } from '@/services/types'
import { API_BASE, staticUrl } from '@/config/api'

interface AssetState {
  // Assets list
  assets: Asset[]
  selectedAssetId: string | null
  
  // Multi-select for batch operations
  selectedAssetIds: Set<string>
  
  // Loading state
  isLoading: boolean
  error: string | null
  
  // Actions
  loadAssets: () => Promise<void>
  setAssets: (assets: Asset[]) => void
  addAsset: (asset: Asset) => void
  updateAsset: (id: string, updates: Partial<Asset>) => void
  removeAsset: (id: string) => void
  removeAssets: (ids: string[]) => void
  selectAsset: (id: string | null) => void
  getSelectedAsset: () => Asset | null
  getAssetById: (id: string) => Asset | null
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearAll: () => void
  
  // Multi-select actions
  toggleSelectAsset: (id: string) => void
  selectAllAssets: () => void
  clearSelection: () => void
  isSelected: (id: string) => boolean
}

export const useAssetStore = create<AssetState>()((set, get) => ({
  assets: [],
  selectedAssetId: null,
  selectedAssetIds: new Set<string>(),
  isLoading: false,
  error: null,
  
  loadAssets: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/api/assets`)
      if (response.ok) {
        const data = await response.json()
        // Transform API response to match frontend types
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const transformedAssets: Asset[] = data.items.map((item: any) => ({
          id: item.id,
          name: item.name,
          description: item.description || '',
          sourceFile: item.sourceFile || '',
          sourceFileUrl: item.sourceFileUrl,
          fileType: item.fileType || 'sbs',
          textures: item.textures || [],
          thumbnailUrl: item.thumbnailUrl 
            ? staticUrl(item.thumbnailUrl)
            : `https://via.placeholder.com/128/6366f1/ffffff?text=${(item.fileType || 'sbs').toUpperCase()}`,
          tags: item.tags || [],
          createdAt: item.createdAt,
          updatedAt: item.updatedAt,
          hasParameters: item.hasParameters || false,
          hasThumbnail: item.hasThumbnail || false,
          hasBakedTextures: item.hasBakedTextures || false,
          metadata: item.metadata || {},
        }))
        set({ assets: transformedAssets, isLoading: false })
      } else {
        set({ error: 'Failed to load assets', isLoading: false })
      }
    } catch (error) {
      console.error('Failed to load assets:', error)
      set({ error: 'Failed to load assets', isLoading: false })
    }
  },
  
  setAssets: (assets: Asset[]) => set({ assets }),
  
  addAsset: (asset: Asset) => set((state) => ({
    assets: [asset, ...state.assets]
  })),
  
  updateAsset: (id: string, updates: Partial<Asset>) => set((state) => ({
    assets: state.assets.map((a) =>
      a.id === id ? { ...a, ...updates } : a
    )
  })),
  
  removeAsset: (id: string) => set((state) => ({
    assets: state.assets.filter((a) => a.id !== id),
    selectedAssetId: state.selectedAssetId === id ? null : state.selectedAssetId,
    selectedAssetIds: new Set([...state.selectedAssetIds].filter(i => i !== id))
  })),
  
  removeAssets: (ids: string[]) => set((state) => ({
    assets: state.assets.filter((a) => !ids.includes(a.id)),
    selectedAssetId: ids.includes(state.selectedAssetId || '') ? null : state.selectedAssetId,
    selectedAssetIds: new Set()
  })),
  
  selectAsset: (id: string | null) => set({ selectedAssetId: id }),
  
  getSelectedAsset: () => {
    const state = get()
    return state.assets.find((a) => a.id === state.selectedAssetId) || null
  },
  
  getAssetById: (id: string) => {
    const state = get()
    return state.assets.find((a) => a.id === id) || null
  },
  
  setLoading: (isLoading: boolean) => set({ isLoading }),
  
  setError: (error: string | null) => set({ error }),
  
  clearAll: () => set({ assets: [], selectedAssetId: null, selectedAssetIds: new Set(), error: null }),
  
  // Multi-select actions
  toggleSelectAsset: (id: string) => set((state) => {
    const newSet = new Set(state.selectedAssetIds)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    return { selectedAssetIds: newSet }
  }),
  
  selectAllAssets: () => set((state) => ({
    selectedAssetIds: new Set(state.assets.map(a => a.id))
  })),
  
  clearSelection: () => set({ selectedAssetIds: new Set() }),
  
  isSelected: (id: string) => get().selectedAssetIds.has(id)
}))
