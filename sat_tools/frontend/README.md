# SAT Frontend - Substance Automation Toolkit 前端工具集

统一的React+TypeScript前端应用，集成参数浏览器、缩略图管理和资产仓库三大功能模块。

## 技术栈

| 类别 | 技术选型 |
|------|----------|
| 框架 | React 18 + TypeScript |
| 构建工具 | Vite |
| 路由 | React Router v6 |
| 状态管理 | Zustand / React Context |
| 样式 | Tailwind CSS |
| HTTP客户端 | Axios |
| UI组件 | 自建 + Headless UI |

---

## 快速开始

### 环境要求

- Node.js >= 18
- npm >= 9 或 pnpm >= 8

### 安装与运行

```bash
# 进入前端目录
cd sat_tools/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

开发服务器默认运行在 `http://localhost:5173`

---

## 项目结构

```
sat_tools/frontend/
├── src/
│   ├── components/           # 共享组件
│   │   ├── ui/              # 基础UI组件
│   │   │   ├── Button.tsx   # 按钮组件
│   │   │   ├── Card.tsx     # 卡片组件
│   │   │   ├── Modal.tsx    # 模态框组件
│   │   │   ├── Table.tsx    # 表格组件
│   │   │   ├── SearchInput.tsx # 搜索输入框
│   │   │   └── TreeView.tsx # 树形视图组件
│   │   └── layout/          # 布局组件
│   │       ├── AppLayout.tsx # 应用主布局
│   │       ├── Header.tsx    # 顶部导航栏
│   │       └── Sidebar.tsx   # 侧边菜单栏
│   ├── views/               # 功能视图
│   │   ├── Dashboard/       # 首页仪表盘
│   │   │   └── index.tsx
│   │   ├── ParameterBrowser/# 参数浏览器 (SAT-001)
│   │   │   ├── index.tsx
│   │   │   ├── ParameterTree.tsx
│   │   │   └── FileSelector.tsx
│   │   ├── ThumbnailManager/# 缩略图管理 (SAT-002)
│   │   │   ├── index.tsx
│   │   │   ├── ThumbnailGrid.tsx
│   │   │   └── MetadataPanel.tsx
│   │   └── AssetRepository/ # 资产仓库 (SAT-003)
│   │       ├── index.tsx
│   │       ├── AssetList.tsx
│   │       └── AssetDetail.tsx
│   ├── services/            # API服务层
│   │   ├── api.ts          # Axios实例配置
│   │   ├── types.ts        # TypeScript类型定义
│   │   ├── parameterApi.ts # 参数相关API
│   │   ├── thumbnailApi.ts # 缩略图相关API
│   │   └── assetApi.ts     # 资产相关API
│   ├── hooks/               # 自定义Hooks
│   │   ├── useApi.ts       # API调用Hook
│   │   └── useTheme.ts     # 主题切换Hook
│   ├── store/               # 状态管理
│   │   └── index.ts
│   ├── routes/              # 路由配置
│   │   └── index.tsx
│   ├── styles/              # 全局样式
│   │   ├── globals.css     # 全局CSS
│   │   └── variables.css   # CSS变量
│   ├── App.tsx             # 应用入口组件
│   └── main.tsx            # 渲染入口
├── public/                  # 静态资源
├── index.html              # HTML模板
├── package.json            # 依赖配置
├── tsconfig.json           # TypeScript配置
├── vite.config.ts          # Vite配置
├── tailwind.config.js      # Tailwind配置
├── .eslintrc.cjs           # ESLint配置
├── .prettierrc             # Prettier配置
└── README.md               # 本文档
```

---

## 功能模块

### Dashboard (/)

集成入口页面，提供：
- 三大功能模块的快捷入口卡片
- 系统状态概览
- 最近操作记录

### Parameter Browser (/parameter-browser)

**对应任务**: SAT-001

参数浏览器，用于查看和分析SBS/SBSAR文件的Graph参数：
- 加载JSON格式的参数数据
- 树状结构展示节点参数
- 多文件快速切换
- 参数搜索和过滤

### Thumbnail Manager (/thumbnail-manager)

**对应任务**: SAT-002

缩略图管理器，用于查看和管理生成的缩略图：
- 网格展示缩略图列表
- 查看嵌入的Metadata信息
- 批量操作支持

### Asset Repository (/asset-repository)

**对应任务**: SAT-003

资产仓库，用于管理已上传的贴图资产：
- 资产列表展示（ID、URL、上传时间）
- 缩略图预览
- 搜索和过滤
- 资产详情查看

---

## 开发指南

### 添加新视图

1. 在 `src/views/` 下创建新目录
2. 创建 `index.tsx` 作为视图入口
3. 在 `src/routes/index.tsx` 中添加路由配置
4. 在 `src/components/layout/Sidebar.tsx` 中添加导航项

```tsx
// src/views/NewFeature/index.tsx
import React from 'react';

const NewFeature: React.FC = () => {
  return (
    <div>
      <h1>New Feature</h1>
    </div>
  );
};

export default NewFeature;
```

```tsx
// src/routes/index.tsx
import { lazy } from 'react';

const NewFeature = lazy(() => import('@/views/NewFeature'));

// 添加路由
{
  path: '/new-feature',
  element: <NewFeature />
}
```

### 使用共享组件

```tsx
import { Button, Card, Modal, SearchInput } from '@/components/ui';

const MyComponent: React.FC = () => {
  return (
    <Card title="示例卡片">
      <SearchInput 
        placeholder="搜索..." 
        onChange={(value) => console.log(value)} 
      />
      <Button variant="primary" onClick={() => {}}>
        点击按钮
      </Button>
    </Card>
  );
};
```

### API调用规范

```tsx
// src/services/types.ts
export interface Asset {
  id: string;
  name: string;
  url: string;
  createdAt: string;
}

// src/services/assetApi.ts
import api from './api';
import type { Asset } from './types';

export const assetApi = {
  getList: () => api.get<Asset[]>('/assets'),
  getById: (id: string) => api.get<Asset>(`/assets/${id}`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Asset>('/assets', formData);
  },
  delete: (id: string) => api.delete(`/assets/${id}`),
};
```

### TypeScript类型规范

- 所有组件Props必须定义类型
- API响应数据必须定义类型
- 使用 `interface` 定义对象类型
- 使用 `type` 定义联合类型和工具类型

```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary', 
  size = 'md',
  ...props 
}) => {
  // ...
};
```

---

## 后端API对接

### 基础配置

API基础URL通过环境变量配置：

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:5000/api

# .env.production
VITE_API_BASE_URL=/api
```

### API端点

| 模块 | 端点 | 方法 | 描述 |
|------|------|------|------|
| Parameter | `/api/parameters` | GET | 获取参数列表 |
| Parameter | `/api/parameters/:file` | GET | 获取指定文件参数 |
| Thumbnail | `/api/thumbnails` | GET | 获取缩略图列表 |
| Thumbnail | `/api/thumbnails/:id/metadata` | GET | 获取缩略图Metadata |
| Asset | `/api/assets` | GET | 获取资产列表 |
| Asset | `/api/assets` | POST | 上传资产 |
| Asset | `/api/assets/:id` | GET | 获取资产详情 |
| Asset | `/api/assets/:id` | DELETE | 删除资产 |

### 错误处理

API服务层统一处理错误：

```tsx
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || '请求失败';
    // 显示错误通知
    console.error(message);
    return Promise.reject(error);
  }
);

export default api;
```

---

## 主题系统

### CSS变量

```css
/* src/styles/variables.css */
:root {
  /* 主色调 */
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  
  /* 背景色 */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f3f4f6;
  
  /* 文字色 */
  --color-text-primary: #111827;
  --color-text-secondary: #6b7280;
  
  /* 边框 */
  --color-border: #e5e7eb;
  
  /* 间距 */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
}

/* 深色模式 */
.dark {
  --color-bg-primary: #111827;
  --color-bg-secondary: #1f2937;
  --color-text-primary: #f9fafb;
  --color-text-secondary: #9ca3af;
  --color-border: #374151;
}
```

### 切换深色模式

```tsx
import { useTheme } from '@/hooks/useTheme';

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <button onClick={toggleTheme}>
      {theme === 'dark' ? '☀️' : '🌙'}
    </button>
  );
};
```

---

## 脚本命令

| 命令 | 描述 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产构建 |
| `npm run lint` | 运行ESLint检查 |
| `npm run lint:fix` | 自动修复ESLint问题 |
| `npm run format` | 运行Prettier格式化 |
| `npm run type-check` | TypeScript类型检查 |

---

## 相关任务

| 任务编号 | 标题 | 关联视图 |
|----------|------|----------|
| SAT-000 | 统一前端集成框架 | 全部 |
| SAT-001 | 参数提取与浏览器 | ParameterBrowser |
| SAT-002 | 缩略图生成与管理 | ThumbnailManager |
| SAT-003 | 贴图烘焙与资产仓库 | AssetRepository |

---

## 注意事项

1. **统一前端原则**: 所有功能视图必须在此项目中开发，禁止创建独立前端项目
2. **组件复用**: 优先使用 `src/components/ui/` 中的共享组件
3. **类型安全**: 所有代码必须通过TypeScript类型检查
4. **代码规范**: 提交前确保通过ESLint和Prettier检查

---

---

## 项目已就绪

所有代码已创建完成，可以通过以下步骤启动:

```bash
# 1. 安装前端依赖
cd sat_tools/frontend
npm install

# 2. 启动前端开发服务器
npm run dev

# 3. 在另一个终端，安装后端依赖
cd sat_tools
pip install -r requirements.txt

# 4. 启动后端服务器
python -m sat_tools.server.app
```

前端访问: http://localhost:5173
后端API: http://localhost:5000/api

---

*最后更新: 2026-01-07*
