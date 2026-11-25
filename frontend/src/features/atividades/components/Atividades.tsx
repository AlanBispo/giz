import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'

import { ErroHttp, mensagemDeErro } from '../../../lib/http'
import { consultaPublicacoes, consultaVinculos, excluirPublicacao, recarregarPublicacoes } from '../api/publicacoes'
import type { Publicacao } from '../types'
import { FormularioPublicacao } from './FormularioPublicacao'

import './atividades.css'

export function Atividades({ usuario, professor, inicio }: {
  usuario: number
  professor: boolean
  inicio: string
}) {
  const [formulario, setFormulario] = useState<Publicacao | 'nova' | null>(null)
  const [confirmacao, setConfirmacao] = useState<Pick<Publicacao, 'id' | 'versao'> | null>(null)
  const lista = useQuery(consultaPublicacoes(usuario))
  const vinculos = useQuery(consultaVinculos(usuario, professor))
  const queryClient = useQueryClient()
  const excluir = useMutation({
    mutationFn: excluirPublicacao,
    onSuccess: async () => {
      await recarregarPublicacoes(queryClient, usuario)
      setConfirmacao(null)
    },
    onError: async (erro) => {
      if (erro instanceof ErroHttp && (erro.status === 409 || erro.status === 404)) {
        await recarregarPublicacoes(queryClient, usuario)
      }
    },
    networkMode: 'always',
  })

  return (
    <div className="area-atividades">
      <Link to={inicio}>Voltar ao início</Link>
      <h1>Atividades e provas</h1>
      {professor && vinculos.isPending && <p role="status">Carregando suas turmas…</p>}
      {professor && vinculos.isError && (
        <>
          <p role="alert">Não foi possível carregar suas turmas.</p>
          <button type="button" onClick={() => void vinculos.refetch()}>Recarregar turmas</button>
        </>
      )}
      {professor && vinculos.data?.length === 0 && <p>Você ainda não tem turmas vinculadas.</p>}
      {professor && Boolean(vinculos.data?.length) && !formulario && (
        <button type="button" onClick={() => setFormulario('nova')}>Nova publicação</button>
      )}
      {professor && vinculos.data && formulario && (
        <FormularioPublicacao
          key={formulario === 'nova' ? 'nova' : formulario.id}
          usuario={usuario}
          vinculos={vinculos.data}
          publicacao={formulario === 'nova' ? undefined : formulario}
          concluir={() => setFormulario(null)}
        />
      )}
      {lista.isPending && <p role="status">Carregando publicações…</p>}
      {lista.isError && (
        <>
          <p role="alert">Não foi possível carregar as publicações.</p>
          <button type="button" onClick={() => void lista.refetch()}>Recarregar publicações</button>
        </>
      )}
      {lista.data?.length === 0 && <p>Nenhuma atividade ou prova publicada.</p>}
      {lista.data && lista.data.length > 0 && (
        <ul className="lista-publicacoes">
          {lista.data.map((item) => (
            <li key={item.id}>
              <h2>{item.titulo}</h2>
              <p>{item.tipo === 'prova' ? 'Prova' : 'Atividade'} · {item.valor.replace('.', ',')} pontos</p>
              <p>{item.nome_turma} · {item.nome_disciplina} · {item.numero_bimestre}º bimestre</p>
              <p><time dateTime={item.data}>{item.data.split('-').reverse().join('/')}</time></p>
              {item.descricao && <p className="descricao-publicacao">{item.descricao}</p>}
              {professor && vinculos.data && !formulario && (
                confirmacao?.id === item.id ? (
                  <div className="acoes-publicacao">
                    <button
                      type="button"
                      disabled={excluir.isPending || confirmacao.versao !== item.versao}
                      onClick={() => excluir.mutate(confirmacao)}
                    >
                      Confirmar exclusão
                    </button>
                    <button type="button" disabled={excluir.isPending} onClick={() => {
                      setConfirmacao(null)
                      excluir.reset()
                    }}>Cancelar</button>
                    {confirmacao.versao !== item.versao
                      ? <p role="alert">A publicação mudou. Cancele e confira a versão atual.</p>
                      : excluir.isError && <p role="alert">{mensagemDeErro(excluir.error)}</p>}
                  </div>
                ) : (
                  <div className="acoes-publicacao">
                    <button type="button" disabled={excluir.isPending} onClick={() => setFormulario(item)}>Editar</button>
                    <button type="button" disabled={excluir.isPending} onClick={() => {
                      excluir.reset()
                      setConfirmacao({ id: item.id, versao: item.versao })
                    }}>Excluir</button>
                  </div>
                )
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
