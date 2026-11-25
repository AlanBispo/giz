import { Link, Navigate, NavLink, Route, Routes } from 'react-router'

import type { Recurso } from '../api/escola'
import { cadastros } from '../cadastros'
import { Cadastro } from './Cadastro'
import { Configuracoes } from './Configuracoes'

import './escola.css'

const recursos = Object.keys(cadastros) as Recurso[]

export function AreaEscolar({ inicio, diretoria }: { inicio: string; diretoria: boolean }) {
  return (
    <div className="area-escolar">
      <Link to={inicio}>Voltar ao início</Link>
      <h1>Escola</h1>
      <nav aria-label="Gestão escolar">
        {recursos.map((recurso) => (
          <NavLink key={recurso} to={`/escola/${recurso}`}>{cadastros[recurso].titulo}</NavLink>
        ))}
        {diretoria && <NavLink to="/escola/regras">Regras de avaliação</NavLink>}
      </nav>
      <Routes>
        {recursos.map((recurso) => (
          <Route key={recurso} path={recurso} element={<Cadastro key={recurso} recurso={recurso} />} />
        ))}
        {diretoria && <Route path="regras" element={<Configuracoes />} />}
        <Route path="*" element={<Navigate to="/escola/pessoas" replace />} />
      </Routes>
    </div>
  )
}
