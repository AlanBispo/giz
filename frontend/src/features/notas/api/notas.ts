import { queryOptions } from '@tanstack/react-query'

import { enviarJson, obterJson } from '../../../lib/http'
import { lancamentoSchema, notasSchema, type Lancamento, type NotaInformada } from '../types'

const rotaLancamento = (id: number) => `/api/notas/publicacoes/${id}/`

export function consultaNotas(usuario: number) {
  return queryOptions({
    queryKey: ['notas', usuario],
    queryFn: async ({ signal }) => notasSchema.parse(await obterJson('/api/notas/', signal)),
    retry: false,
    networkMode: 'always',
    gcTime: 0,
  })
}

export function consultaLancamento(usuario: number, id: number) {
  return queryOptions({
    queryKey: ['notas', usuario, id],
    queryFn: async ({ signal }) => lancamentoSchema.parse(await obterJson(rotaLancamento(id), signal)),
    retry: false,
    networkMode: 'always',
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    gcTime: 0,
  })
}

export async function salvarLancamento(
  id: number, versao: number, notas: NotaInformada[],
): Promise<Lancamento> {
  return lancamentoSchema.parse(await enviarJson(rotaLancamento(id), 'PATCH', { versao, notas }))
}
