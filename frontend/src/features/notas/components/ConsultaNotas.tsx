import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'

import { consultaNotas } from '../api/notas'

import './notas.css'

export function ConsultaNotas({ usuario, gestao, inicio }: {
  usuario: number
  gestao: boolean
  inicio: string
}) {
  const consulta = useQuery(consultaNotas(usuario))
  return (
    <div className="area-notas">
      <Link to={inicio}>Voltar ao início</Link>
      <h1>{gestao ? 'Notas da escola' : 'Minhas notas'}</h1>
      {consulta.isPending && <p role="status">Carregando notas…</p>}
      {consulta.isError && (
        <>
          <p role="alert">Não foi possível carregar as notas.</p>
          <button type="button" onClick={() => void consulta.refetch()}>Tentar novamente</button>
        </>
      )}
      {consulta.data?.length === 0 && <p>Nenhuma nota lançada.</p>}
      {consulta.data && consulta.data.length > 0 && (
        <div className="tabela-notas">
          <table aria-label={gestao ? 'Notas da escola' : 'Minhas notas'}>
            <thead>
              <tr>
                {gestao && <th scope="col">Aluno</th>}
                <th scope="col">Publicação</th>
                <th scope="col">Turma e disciplina</th>
                <th scope="col">Bimestre</th>
                <th scope="col">Nota</th>
              </tr>
            </thead>
            <tbody>
              {consulta.data.map(({ id, aluno, matricula, publicacao, valor }) => (
                <tr key={id}>
                  {gestao && <td>{aluno}<small>Matrícula {matricula}</small></td>}
                  <th scope="row">
                    {publicacao.titulo}
                    <small>
                      {publicacao.tipo === 'prova' ? 'Prova' : 'Atividade'} ·{' '}
                      <time dateTime={publicacao.data}>{publicacao.data.split('-').reverse().join('/')}</time>
                    </small>
                  </th>
                  <td>{publicacao.nome_turma} · {publicacao.nome_disciplina}</td>
                  <td>{publicacao.numero_bimestre}º</td>
                  <td>{valor.replace('.', ',')} / {publicacao.valor.replace('.', ',')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
