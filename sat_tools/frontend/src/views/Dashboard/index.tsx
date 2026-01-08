import { Link } from 'react-router-dom'
import { FileJson, Image, Database, ArrowRight, Activity, Clock, CheckCircle } from 'lucide-react'
import { Card } from '@/components/ui'

const modules = [
  {
    title: '参数浏览器',
    description: '读取SBS/SBSAR文件，提取Graph参数并以树状结构展示',
    icon: FileJson,
    path: '/parameter-browser',
    color: 'from-blue-500 to-blue-600',
    stats: { label: '已解析文件', value: '0' },
  },
  {
    title: '缩略图管理',
    description: '为Substance文件生成缩略图，支持嵌入和查看Metadata',
    icon: Image,
    path: '/thumbnail-manager',
    color: 'from-purple-500 to-purple-600',
    stats: { label: '已生成缩略图', value: '0' },
  },
  {
    title: '资产仓库',
    description: '烘焙贴图并上传到仓库，管理和浏览已上传资产',
    icon: Database,
    path: '/asset-repository',
    color: 'from-emerald-500 to-emerald-600',
    stats: { label: '仓库资产', value: '0' },
  },
]

const recentActivities = [
  { id: 1, action: '系统已就绪', time: '刚刚', status: 'success' },
]

const Dashboard = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-white">
          Dashboard
        </h1>
        <p className="mt-1 text-surface-500 dark:text-surface-400">
          欢迎使用 SAT Tools - Substance Automation Toolkit 前端工具集
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <Activity className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-surface-900 dark:text-white">
              3
            </p>
            <p className="text-sm text-surface-500 dark:text-surface-400">
              功能模块
            </p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
            <CheckCircle className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-surface-900 dark:text-white">
              就绪
            </p>
            <p className="text-sm text-surface-500 dark:text-surface-400">
              系统状态
            </p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <Clock className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-surface-900 dark:text-white">
              0
            </p>
            <p className="text-sm text-surface-500 dark:text-surface-400">
              今日任务
            </p>
          </div>
        </Card>
      </div>

      {/* Module Cards */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-surface-900 dark:text-white">
          功能模块
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          {modules.map((module) => {
            const Icon = module.icon
            return (
              <Link key={module.path} to={module.path}>
                <Card
                  hoverable
                  className="group h-full transition-all hover:border-primary-200 dark:hover:border-primary-800"
                >
                  <div className="flex items-start justify-between">
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${module.color}`}
                    >
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <ArrowRight className="h-5 w-5 text-surface-300 transition-transform group-hover:translate-x-1 group-hover:text-primary-500 dark:text-surface-600" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-surface-900 dark:text-white">
                    {module.title}
                  </h3>
                  <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
                    {module.description}
                  </p>
                  <div className="mt-4 flex items-center gap-2 rounded-lg bg-surface-50 px-3 py-2 dark:bg-surface-800">
                    <span className="text-xs text-surface-500 dark:text-surface-400">
                      {module.stats.label}
                    </span>
                    <span className="font-medium text-surface-900 dark:text-white">
                      {module.stats.value}
                    </span>
                  </div>
                </Card>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-surface-900 dark:text-white">
          最近活动
        </h2>
        <Card padding="none">
          <div className="divide-y dark:divide-surface-800">
            {recentActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-center justify-between px-6 py-4"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`h-2 w-2 rounded-full ${
                      activity.status === 'success'
                        ? 'bg-emerald-500'
                        : activity.status === 'pending'
                        ? 'bg-yellow-500'
                        : 'bg-surface-300'
                    }`}
                  />
                  <span className="text-surface-900 dark:text-white">
                    {activity.action}
                  </span>
                </div>
                <span className="text-sm text-surface-500 dark:text-surface-400">
                  {activity.time}
                </span>
              </div>
            ))}
            {recentActivities.length === 0 && (
              <div className="px-6 py-8 text-center text-surface-500">
                暂无活动记录
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
