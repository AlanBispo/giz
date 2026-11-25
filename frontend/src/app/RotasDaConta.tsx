import { Navigate, Route, Routes } from 'react-router'

import { Inicio } from '../features/contas/components/Inicio'
import { Login } from '../features/contas/components/Login'
import { useSessao } from '../features/contas/hooks/useSessao'
import { perfis } from '../features/contas/types'

export function RotasDaConta() {
  const sessao = useSessao()

  if (sessao.isPending) {
    return <p role="status">Verificando a sessão…</p>
  }

  if (sessao.isError) {
    return (
      <>
        <p role="alert">Não foi possível verificar a sessão.</p>
        <button type="button" onClick={() => void sessao.refetch()} disabled={sessao.isFetching}>
          Tentar novamente
        </button>
      </>
    )
  }

  const usuario = sessao.data
  const destino = usuario ? `/${usuario.perfil}` : '/login'

  return (
    <Routes>
      <Route path="login" element={usuario ? <Navigate to={destino} replace /> : <Login />} />
      {Object.keys(perfis).map((perfil) => (
        <Route
          key={perfil}
          path={perfil}
          element={usuario?.perfil === perfil
            ? <Inicio usuario={usuario} />
            : <Navigate to={destino} replace />}
        />
      ))}
      <Route path="*" element={<Navigate to={destino} replace />} />
    </Routes>
  )
}
