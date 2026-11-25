import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router'

import { EstadoDaApi } from '../features/saude/components/EstadoDaApi'
import { RotasDaConta } from './RotasDaConta'

import './app.css'

const queryClient = new QueryClient()

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <main>
          <Routes>
            <Route path="/saude" element={<><h1>Saúde do Giz</h1><EstadoDaApi /></>} />
            <Route path="/*" element={<RotasDaConta />} />
          </Routes>
        </main>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
