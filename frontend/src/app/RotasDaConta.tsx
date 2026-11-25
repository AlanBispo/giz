import { Link, Navigate, Route, Routes } from 'react-router'

import { Atividades } from '../features/atividades/components/Atividades'
import { Inicio } from '../features/contas/components/Inicio'
import { Login } from '../features/contas/components/Login'
import { useSessao } from '../features/contas/hooks/useSessao'
import { perfis } from '../features/contas/types'
import { AreaEscolar } from '../features/escola/components/AreaEscolar'
import { ConsultaNotas } from '../features/notas/components/ConsultaNotas'
import { LancamentoNotas } from '../features/notas/components/LancamentoNotas'

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
  const diretoria = usuario?.perfil === 'diretoria'
  const podeGerir = diretoria || usuario?.perfil === 'coordenacao'
  const podeVerAtividades = usuario?.perfil === 'professor' || usuario?.perfil === 'aluno'
  const podeConsultarNotas = podeGerir || usuario?.perfil === 'aluno'

  return (
    <Routes>
      <Route path="login" element={usuario ? <Navigate to={destino} replace /> : <Login />} />
      <Route path="escola/*" element={podeGerir
        ? <AreaEscolar inicio={destino} diretoria={diretoria} />
        : <Navigate to={destino} replace />} />
      <Route path="atividades" element={usuario && podeVerAtividades
        ? <Atividades key={usuario.id} usuario={usuario.id} professor={usuario.perfil === 'professor'} inicio={destino} />
        : <Navigate to={destino} replace />} />
      <Route path="notas" element={usuario && podeConsultarNotas
        ? <ConsultaNotas key={usuario.id} usuario={usuario.id} gestao={podeGerir} inicio={destino} />
        : <Navigate to={destino} replace />} />
      <Route path="notas/:publicacaoId" element={usuario?.perfil === 'professor'
        ? <LancamentoNotas key={usuario.id} usuario={usuario.id} />
        : <Navigate to={destino} replace />} />
      {Object.keys(perfis).map((perfil) => (
        <Route
          key={perfil}
          path={perfil}
          element={usuario?.perfil === perfil
            ? <>
                <Inicio usuario={usuario} />
                {podeGerir && <p><Link to="/escola">Gestão escolar</Link></p>}
                {podeVerAtividades && <p><Link to="/atividades">Atividades e provas</Link></p>}
                {podeConsultarNotas && <p><Link to="/notas">{podeGerir ? 'Notas da escola' : 'Minhas notas'}</Link></p>}
              </>
            : <Navigate to={destino} replace />}
        />
      ))}
      <Route path="*" element={<Navigate to={destino} replace />} />
    </Routes>
  )
}
