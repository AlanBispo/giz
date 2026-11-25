import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { EstadoDaApi } from '../features/saude/components/EstadoDaApi'

import './app.css'

const queryClient = new QueryClient()

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <main>
        <h1>Giz</h1>
        <EstadoDaApi />
      </main>
    </QueryClientProvider>
  )
}
