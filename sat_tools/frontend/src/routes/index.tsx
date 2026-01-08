import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'

// Lazy load views for code splitting
const Dashboard = lazy(() => import('@/views/Dashboard'))
const ParameterBrowser = lazy(() => import('@/views/ParameterBrowser'))
const ThumbnailManager = lazy(() => import('@/views/ThumbnailManager'))
const AssetRepository = lazy(() => import('@/views/AssetRepository'))

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Dashboard />,
  },
  {
    path: '/parameter-browser',
    element: <ParameterBrowser />,
  },
  {
    path: '/thumbnail-manager',
    element: <ThumbnailManager />,
  },
  {
    path: '/asset-repository',
    element: <AssetRepository />,
  },
]

export const navItems = [
  {
    path: '/',
    label: 'Dashboard',
    icon: 'LayoutDashboard',
  },
  {
    path: '/parameter-browser',
    label: '参数浏览器',
    icon: 'FileJson',
  },
  {
    path: '/thumbnail-manager',
    label: '缩略图管理',
    icon: 'Image',
  },
  {
    path: '/asset-repository',
    label: '资产仓库',
    icon: 'Database',
  },
]
