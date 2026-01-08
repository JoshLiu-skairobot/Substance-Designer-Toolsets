import { Suspense } from 'react'
import { useRoutes } from 'react-router-dom'
import { routes } from './routes'
import AppLayout from './components/layout/AppLayout'

function App() {
  const element = useRoutes(routes)

  return (
    <AppLayout>
      <Suspense
        fallback={
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          </div>
        }
      >
        {element}
      </Suspense>
    </AppLayout>
  )
}

export default App
