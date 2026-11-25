import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import { ErroHttp, mensagemDeErro } from '../../../lib/http'
import { consultaSaldo, recarregarPublicacoes, salvarPublicacao } from '../api/publicacoes'
import { type Publicacao, tipoSchema, type Vinculo } from '../types'

const schema = z.object({
  titulo: z.string().trim().min(1, 'Informe o título.').max(150),
  descricao: z.string().trim().max(5000),
  data: z.iso.date('Informe uma data válida.'),
  tipo: tipoSchema,
  vinculo: z.string().min(1, 'Selecione uma turma e disciplina.'),
  bimestre: z.string().min(1, 'Selecione o bimestre.'),
  valor: z.string().trim(),
}).refine((dados) => dados.tipo === 'prova' || /^\d{1,3}([.,]\d{1,2})?$/.test(dados.valor), {
  path: ['valor'],
  error: 'Informe um valor entre 0 e 999,99.',
})

const chaveVinculo = (vinculo: Pick<Vinculo, 'turma' | 'disciplina'>) =>
  `${vinculo.turma}:${vinculo.disciplina}`

type Formulario = z.infer<typeof schema>

export function FormularioPublicacao({ usuario, vinculos, publicacao, concluir }: {
  usuario: number
  vinculos: Vinculo[]
  publicacao?: Publicacao
  concluir: () => void
}) {
  const queryClient = useQueryClient()
  const { control, register, setValue, handleSubmit, formState: { errors, isSubmitting, isDirty } } =
    useForm<Formulario>({
      resolver: zodResolver(schema),
      defaultValues: {
        titulo: publicacao?.titulo ?? '',
        descricao: publicacao?.descricao ?? '',
        data: publicacao?.data ?? '',
        tipo: publicacao?.tipo ?? 'atividade',
        vinculo: publicacao ? chaveVinculo(publicacao) : vinculos.length === 1 ? chaveVinculo(vinculos[0]) : '',
        bimestre: publicacao ? String(publicacao.bimestre) : '',
        valor: publicacao?.tipo === 'atividade' ? publicacao.valor.replace('.', ',') : '',
      },
    })
  const [chave, bimestre, tipo] = useWatch({ control, name: ['vinculo', 'bimestre', 'tipo'] })
  const vinculo = vinculos.find((opcao) => chaveVinculo(opcao) === chave)
  const periodo = vinculo?.bimestres.some(({ id }) => String(id) === bimestre)
    ? { turma: vinculo.turma, disciplina: vinculo.disciplina, bimestre: Number(bimestre) }
    : null
  const opcoesSaldo = consultaSaldo(usuario, periodo)
  const saldo = useQuery(opcoesSaldo)
  const gravar = useMutation({
    mutationFn: (dados: Formulario) => {
      if (!periodo) throw new Error('Selecione um bimestre do ano letivo.')
      return salvarPublicacao({
        ...periodo,
        titulo: dados.titulo,
        descricao: dados.descricao,
        tipo: dados.tipo,
        data: dados.data,
        versao: publicacao?.versao,
        ...(dados.tipo === 'atividade' ? { valor: dados.valor.replace(',', '.') } : {}),
      }, publicacao?.id)
    },
    onSuccess: async () => {
      await recarregarPublicacoes(queryClient, usuario)
      concluir()
    },
    onError: async (erro) => {
      if (!(erro instanceof ErroHttp)) return
      if (erro.status === 409 || erro.status === 404) {
        await recarregarPublicacoes(queryClient, usuario)
      } else if (erro.status === 400 && periodo && erro.detalhes
        && typeof erro.detalhes === 'object' && 'valor' in erro.detalhes) {
        await queryClient.cancelQueries({ queryKey: opcoesSaldo.queryKey, exact: true })
        await saldo.refetch()
      }
    },
    networkMode: 'always',
  })
  const pontosProva = publicacao?.tipo === 'prova' ? publicacao.valor : saldo.data?.pontos_prova
  const statusErro = gravar.error instanceof ErroHttp ? gravar.error.status : undefined
  const edicaoDesatualizada = statusErro === 404 || statusErro === 409

  return (
    <section>
      <h2>{publicacao ? 'Editar publicação' : 'Nova publicação'}</h2>
      <form noValidate onSubmit={handleSubmit((dados) => gravar.mutateAsync(dados).catch(() => undefined))}>
        <fieldset disabled={isSubmitting}>
          <legend>Turma e período</legend>
          <label>
            Turma e disciplina
            <select {...register('vinculo', { onChange: () => setValue('bimestre', '', { shouldDirty: true }) })}>
              <option value="">Selecione</option>
              {vinculos.map((opcao) => (
                <option key={chaveVinculo(opcao)} value={chaveVinculo(opcao)}>
                  {opcao.nome_turma} — {opcao.nome_disciplina}
                </option>
              ))}
            </select>
            {errors.vinculo && <span role="alert">{errors.vinculo.message}</span>}
          </label>
          <label>
            Bimestre
            <select {...register('bimestre')} disabled={!vinculo?.bimestres.length}>
              <option value="">
                {vinculo && !vinculo.bimestres.length ? 'Nenhum bimestre cadastrado' : 'Selecione'}
              </option>
              {vinculo?.bimestres.map(({ id, numero }) => (
                <option key={id} value={id}>{numero}º bimestre</option>
              ))}
            </select>
            {errors.bimestre && <span role="alert">{errors.bimestre.message}</span>}
          </label>
          {periodo && saldo.isPending && <p role="status">Consultando saldo…</p>}
          {periodo && saldo.isError && (
            <>
              <p role="alert">Não foi possível consultar o saldo.</p>
              <button type="button" onClick={() => void saldo.refetch()}>Tentar novamente</button>
            </>
          )}
          {periodo && saldo.data && (
            <p><strong>{saldo.data.saldo.replace('.', ',')}</strong> pontos de atividades disponíveis.</p>
          )}
        </fieldset>
        <fieldset disabled={isSubmitting}>
          <legend>Publicação</legend>
          <label>
            Tipo
            <select {...register('tipo')}>
              <option value="atividade">Atividade</option>
              <option value="prova">Prova</option>
            </select>
          </label>
          <label>
            Título
            <input {...register('titulo')} maxLength={150} />
            {errors.titulo && <span role="alert">{errors.titulo.message}</span>}
          </label>
          <label>
            Descrição
            <textarea {...register('descricao')} rows={3} maxLength={5000} />
            {errors.descricao && <span role="alert">{errors.descricao.message}</span>}
          </label>
          <label>
            Data
            <input type="date" {...register('data')} />
            {errors.data && <span role="alert">{errors.data.message}</span>}
          </label>
          {tipo === 'atividade' ? (
            <label>
              Valor em pontos
              <input inputMode="decimal" {...register('valor')} />
              {errors.valor && <span role="alert">{errors.valor.message}</span>}
            </label>
          ) : (
            <p>{pontosProva ? `Valor da prova: ${pontosProva.replace('.', ',')} pontos.` : 'Selecione o período para ver o valor da prova.'}</p>
          )}
        </fieldset>
        {gravar.isError && (
          <p role="alert">
            {statusErro === 404
              ? 'A publicação não está mais disponível. Volte à lista para continuar.'
              : mensagemDeErro(gravar.error)}
          </p>
        )}
        <div className="acoes-publicacao">
          <button
            type="submit"
            disabled={!periodo || isSubmitting || edicaoDesatualizada || Boolean(publicacao && !isDirty)}
          >
            {isSubmitting ? 'Salvando…' : publicacao ? 'Salvar alterações' : 'Publicar'}
          </button>
          <button type="button" onClick={concluir} disabled={isSubmitting}>
            {edicaoDesatualizada ? 'Voltar à lista' : 'Cancelar'}
          </button>
        </div>
      </form>
    </section>
  )
}
