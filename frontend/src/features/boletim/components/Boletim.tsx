import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'

import { consultaBoletim, consultaTurmas } from '../api/boletim'

import './boletim.css'

export function Boletim({ usuario, gestao, inicio }: {
  usuario: number
  gestao: boolean
  inicio: string
}) {
  return (
    <div className="area-boletim">
      <Link to={inicio}>Voltar ao início</Link>
      <h1>{gestao ? 'Boletim por turma' : 'Meu boletim'}</h1>
      {gestao ? <SeletorDeTurma usuario={usuario} /> : <ResultadoBoletim usuario={usuario} />}
    </div>
  )
}

function SeletorDeTurma({ usuario }: { usuario: number }) {
  const [turma, selecionarTurma] = useState('')
  const consulta = useQuery(consultaTurmas(usuario))
  if (consulta.isPending) return <p role="status">Carregando turmas…</p>
  if (consulta.isError) {
    return (
      <>
        <p role="alert">Não foi possível carregar as turmas.</p>
        <button type="button" onClick={() => void consulta.refetch()}>Tentar novamente</button>
      </>
    )
  }
  if (!consulta.data.length) return <p>Nenhuma turma cadastrada.</p>

  return (
    <>
      <label>
        Turma
        <select value={turma} onChange={(evento) => selecionarTurma(evento.target.value)}>
          <option value="">Selecione uma turma</option>
          {consulta.data.map(({ id, nome, ano }) => (
            <option key={id} value={id}>{nome} ({ano})</option>
          ))}
        </select>
      </label>
      {turma && <ResultadoBoletim usuario={usuario} turma={turma} />}
    </>
  )
}

function notaFormatada(valor: string | null): string {
  return valor?.replace('.', ',') ?? '—'
}

function ResultadoBoletim({ usuario, turma }: { usuario: number; turma?: string }) {
  const consulta = useQuery(consultaBoletim(usuario, turma))
  if (consulta.isPending) return <p role="status">Carregando boletim…</p>
  if (consulta.isError) {
    return (
      <>
        <p role="alert">Não foi possível carregar o boletim.</p>
        <button type="button" onClick={() => void consulta.refetch()}>Tentar novamente</button>
      </>
    )
  }

  const { media_minima, linhas } = consulta.data
  return (
    <>
      <p>Média mínima da escola <strong>{notaFormatada(media_minima)}</strong></p>
      {linhas.length === 0 ? <p>Nenhuma nota lançada.</p> : (
        <div className="tabela-boletim">
          <table aria-label={turma ? 'Boletim da turma selecionada' : 'Meu boletim'}>
            <thead>
              <tr>
                {turma ? <th scope="col">Aluno</th> : <th scope="col">Turma</th>}
                <th scope="col">Disciplina</th>
                <th scope="col">Bimestre</th>
                <th scope="col">Atividades</th>
                <th scope="col">Prova</th>
                <th scope="col">Nota</th>
                <th scope="col">Situação</th>
              </tr>
            </thead>
            <tbody>
              {linhas.map((linha) => (
                <tr key={JSON.stringify([linha.matricula, linha.ano, linha.disciplina, linha.bimestre])}>
                  <th scope="row">
                    {turma ? <>{linha.aluno}<small>Matrícula {linha.matricula}</small></>
                      : <>{linha.turma}<small>{linha.ano}</small></>}
                  </th>
                  <td>{linha.disciplina}</td>
                  <td>{linha.bimestre}º</td>
                  <td>{notaFormatada(linha.atividades)}</td>
                  <td>{notaFormatada(linha.prova)}</td>
                  <td>{notaFormatada(linha.nota)}</td>
                  <td>{linha.situacao === 'aprovado' ? 'Aprovado' : 'Abaixo da média'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
