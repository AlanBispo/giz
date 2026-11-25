import { queryOptions } from '@tanstack/react-query'

import { obterJson } from '../../../lib/http'
import { boletimSchema, turmasSchema } from '../types'

export function consultaTurmas(usuario: number) {
  return queryOptions({
    queryKey: ['boletim', usuario, 'turmas'],
    queryFn: async ({ signal }) => turmasSchema.parse(await obterJson('/api/escola/turmas/', signal)),
    retry: false,
    networkMode: 'always',
    gcTime: 0,
  })
}

export function consultaBoletim(usuario: number, turma?: string) {
  const caminho = turma ? `/api/boletim/turmas/${turma}/` : '/api/boletim/meu/'
  return queryOptions({
    queryKey: ['boletim', usuario, 'consulta', turma],
    queryFn: async ({ signal }) => boletimSchema.parse(await obterJson(caminho, signal)),
    retry: false,
    networkMode: 'always',
    gcTime: 0,
  })
}
