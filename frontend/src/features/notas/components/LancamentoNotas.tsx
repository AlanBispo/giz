import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useParams } from 'react-router'
import { z } from 'zod'

import { ErroHttp, mensagemDeErro } from '../../../lib/http'
import { consultaLancamento, salvarLancamento } from '../api/notas'
import type { Lancamento, NotaInformada } from '../types'

import './notas.css'

type Formulario = { notas: NotaInformada[] }

function FormularioNotas({ lancamento, bloqueado, salvando, salvar }: {
  lancamento: Lancamento
  bloqueado: boolean
  salvando: boolean
  salvar: (notas: NotaInformada[]) => void
}) {
  const maximo = lancamento.publicacao.valor.replace('.', ',')
  const schema = z.object({
    notas: z.array(z.object({
      matricula: z.number().int(),
      valor: z.string().trim().refine((valor) => valor === '' || (
        /^\d{1,3}([.,]\d{1,2})?$/.test(valor) &&
        Number(valor.replace(',', '.')) <= Number(lancamento.publicacao.valor)
      ), `Informe uma nota entre 0 e ${maximo}, com até duas casas decimais.`),
    })),
  }).superRefine(({ notas }, ctx) => {
    notas.forEach(({ valor }, indice) => {
      if (valor === '' && lancamento.alunos[indice]?.valor != null) {
        ctx.addIssue({ code: 'custom', path: ['notas', indice, 'valor'], message: 'Informe a nota corrigida.' })
      }
    })
  })
  const { register, handleSubmit, formState: { errors, isDirty, dirtyFields } } = useForm<Formulario>({
    resolver: zodResolver(schema),
    defaultValues: {
      notas: lancamento.alunos.map(({ matricula, valor }) => ({
        matricula, valor: valor?.replace('.', ',') ?? '',
      })),
    },
  })

  function enviar({ notas }: Formulario) {
    const alteracoes = notas.flatMap(({ matricula, valor }, indice) => (
      dirtyFields.notas?.[indice]?.valor && valor !== ''
        ? [{ matricula, valor: valor.replace(',', '.') }]
        : []
    ))
    if (alteracoes.length) salvar(alteracoes)
  }

  if (!lancamento.alunos.length) return <p>Nenhum aluno matriculado nesta turma.</p>

  return (
    <form noValidate onSubmit={handleSubmit(enviar)}>
      <div className="tabela-notas">
        <table aria-label="Notas da turma">
          <thead><tr><th scope="col">Aluno</th><th scope="col">Nota de 0 a {maximo}</th></tr></thead>
          <tbody>
            {lancamento.alunos.map(({ matricula, nome }, indice) => {
              const erro = errors.notas?.[indice]?.valor
              return (
                <tr key={matricula}>
                  <th scope="row">{nome}<small>Matrícula {matricula}</small></th>
                  <td>
                    <input
                      {...register(`notas.${indice}.valor`)}
                      aria-label={`Nota de ${nome}, matrícula ${matricula}`}
                      aria-invalid={Boolean(erro)}
                      aria-describedby={erro ? `erro-nota-${matricula}` : undefined}
                      inputMode="decimal"
                      placeholder="Sem nota"
                      disabled={salvando}
                    />
                    {erro && <p id={`erro-nota-${matricula}`} role="alert">{erro.message}</p>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <button type="submit" disabled={!isDirty || bloqueado || salvando}>
        {salvando ? 'Salvando…' : 'Salvar notas'}
      </button>
    </form>
  )
}

function FolhaDeNotas({ usuario, id }: { usuario: number; id: number }) {
  const opcoes = consultaLancamento(usuario, id)
  const consulta = useQuery(opcoes)
  const queryClient = useQueryClient()
  const gravar = useMutation({
    mutationFn: ({ versao, notas }: { versao: number; notas: NotaInformada[] }) =>
      salvarLancamento(id, versao, notas),
    onSuccess: async (lancamento) => {
      await queryClient.cancelQueries({ queryKey: opcoes.queryKey, exact: true })
      queryClient.setQueryData(opcoes.queryKey, lancamento)
    },
    networkMode: 'always',
    gcTime: 0,
  })
  const status = gravar.error instanceof ErroHttp ? gravar.error.status : null
  const lancamento = consulta.data
  const matriculas = lancamento?.alunos.map(({ matricula }) => matricula).join(',')

  return (
    <div className="area-notas">
      <Link to="/atividades">Voltar às atividades</Link>
      <h1>Lançar notas</h1>
      {consulta.isPending && <p role="status">Carregando a turma…</p>}
      {consulta.isError && (
        <>
          <p role="alert">{consulta.error instanceof ErroHttp && consulta.error.status === 404
            ? 'Publicação indisponível para lançamento.'
            : 'Não foi possível carregar a turma.'}</p>
          <button type="button" onClick={() => void consulta.refetch()}>Tentar novamente</button>
        </>
      )}
      {lancamento && (
        <>
          <h2>{lancamento.publicacao.titulo}</h2>
          <p>
            {lancamento.publicacao.nome_turma} · {lancamento.publicacao.nome_disciplina} ·{' '}
            {lancamento.publicacao.numero_bimestre}º bimestre
          </p>
          {gravar.isError && (
            <p role="alert">{status === 404
              ? 'A publicação não está mais disponível para lançamento.'
              : mensagemDeErro(gravar.error, { notas: 'Notas', versao: 'Versão' })}</p>
          )}
          {status === 409 && (
            <button type="button" disabled={consulta.isFetching} onClick={async () => {
              const resultado = await consulta.refetch()
              if (resultado.isSuccess) gravar.reset()
            }}>Descartar alterações e carregar notas atuais</button>
          )}
          {gravar.isSuccess && <p role="status">Notas salvas.</p>}
          <FormularioNotas
            key={`${lancamento.publicacao.versao}:${matriculas}`}
            lancamento={lancamento}
            bloqueado={status === 409 || status === 404 || consulta.isError}
            salvando={gravar.isPending || consulta.isFetching}
            salvar={(notas) => gravar.mutate({ versao: lancamento.publicacao.versao, notas })}
          />
        </>
      )}
    </div>
  )
}

export function LancamentoNotas({ usuario }: { usuario: number }) {
  const id = Number(useParams().publicacaoId)
  if (!Number.isSafeInteger(id) || id < 1) {
    return <><p role="alert">Publicação inválida.</p><Link to="/atividades">Voltar às atividades</Link></>
  }
  return <FolhaDeNotas key={id} usuario={usuario} id={id} />
}
