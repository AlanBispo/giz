import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ErroHttp, mensagemDeErro } from '../../../lib/http'
import { consultaRegras, type Regras, salvarRegras, type ValoresRegras } from '../api/escola'

const decimal = z.string().trim()
  .regex(/^\d{1,3}([.,]\d{1,2})?$/, 'Informe um número de 0 a 999,99.')
  .transform((valor) => valor.replace(',', '.'))

const schema = z.object({
  media_minima: decimal,
  pontos_atividades: decimal,
  pontos_prova: decimal,
})

const campos = [
  ['media_minima', 'Média mínima para aprovação'],
  ['pontos_atividades', 'Pontos de atividades por bimestre'],
  ['pontos_prova', 'Pontos da prova por bimestre'],
] as const

function valoresDoFormulario(regras: Regras): ValoresRegras {
  return {
    media_minima: regras.media_minima,
    pontos_atividades: regras.pontos_atividades,
    pontos_prova: regras.pontos_prova,
  }
}

function FormularioRegras({ regras }: { regras: Regras }) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState: { dirtyFields, errors, isDirty } } = useForm<ValoresRegras>({
    defaultValues: valoresDoFormulario(regras),
    resolver: zodResolver(schema),
  })
  useEffect(() => {
    reset(valoresDoFormulario(regras), { keepDirtyValues: true })
  }, [regras, reset])

  const gravar = useMutation({
    mutationFn: salvarRegras,
    networkMode: 'always',
    gcTime: 0,
    onSuccess: async (atualizadas) => {
      await queryClient.cancelQueries({ queryKey: consultaRegras.queryKey, exact: true })
      queryClient.setQueryData(consultaRegras.queryKey, atualizadas)
      reset(valoresDoFormulario(atualizadas))
    },
  })

  function enviar(dados: ValoresRegras) {
    const alteracoes: Partial<ValoresRegras> = {}
    for (const [nome] of campos) {
      if (dirtyFields[nome]) alteracoes[nome] = dados[nome]
    }
    gravar.mutate(alteracoes)
  }

  return (
    <form className="regras-escolares" noValidate onSubmit={handleSubmit(enviar)}>
      {campos.map(([nome, rotulo]) => (
        <label key={nome}>
          {rotulo}
          <input
            inputMode="decimal"
            disabled={gravar.isPending}
            aria-invalid={Boolean(errors[nome])}
            aria-describedby={errors[nome] ? `erro-${nome}` : undefined}
            {...register(nome)}
          />
          {errors[nome] && <span id={`erro-${nome}`} role="alert">{errors[nome]?.message}</span>}
        </label>
      ))}
      {gravar.isError && <p role="alert">{mensagemDeErro(gravar.error, Object.fromEntries(campos))}</p>}
      {gravar.isSuccess && !isDirty && <p role="status">Regras salvas.</p>}
      <button type="submit" disabled={gravar.isPending || !isDirty}>
        {gravar.isPending ? 'Salvando…' : 'Salvar regras'}
      </button>
    </form>
  )
}

export function Configuracoes() {
  const regras = useQuery(consultaRegras)
  return (
    <section>
      <h2>Regras de avaliação</h2>
      {regras.isPending && <p role="status">Carregando regras…</p>}
      {regras.isError && (
        <>
          <p role="alert">
            {regras.error instanceof ErroHttp && regras.error.status === 404
              ? 'Cadastre a escola no admin do Django.'
              : 'Não foi possível carregar as regras.'}
          </p>
          <button type="button" onClick={() => void regras.refetch()}>Tentar novamente</button>
        </>
      )}
      {regras.data && <><p>{regras.data.nome}</p><FormularioRegras regras={regras.data} /></>}
    </section>
  )
}
