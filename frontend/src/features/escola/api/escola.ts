import { queryOptions } from '@tanstack/react-query'
import { z } from 'zod'

import { enviarJson, obterJson } from '../../../lib/http'

const registrosSchema = z.array(z.object({ id: z.number().int() })
  .catchall(z.union([z.string(), z.number()])))

export type Registro = z.infer<typeof registrosSchema>[number]

export type Recurso =
  | 'pessoas' | 'anos-letivos' | 'bimestres' | 'turmas'
  | 'disciplinas' | 'vinculos' | 'matriculas'

const regrasSchema = z.object({
  nome: z.string(),
  media_minima: z.string(),
  pontos_atividades: z.string(),
  pontos_prova: z.string(),
})

export type Regras = z.infer<typeof regrasSchema>
export type ValoresRegras = Omit<Regras, 'nome'>

export function consultaCadastro(recurso: Recurso) {
  return queryOptions({
    queryKey: ['escola', recurso] as const,
    queryFn: async ({ signal }) => registrosSchema.parse(
      await obterJson(`/api/escola/${recurso}/`, signal),
    ),
    networkMode: 'always',
    retry: false,
    gcTime: 0,
  })
}

export async function cadastrar(recurso: Recurso, dados: Record<string, string>): Promise<void> {
  await enviarJson(`/api/escola/${recurso}/`, 'POST', dados)
}

export const consultaRegras = queryOptions({
  queryKey: ['escola', 'regras'] as const,
  queryFn: async ({ signal }) => regrasSchema.parse(await obterJson('/api/escola/regras/', signal)),
  networkMode: 'always',
  retry: false,
  gcTime: 0,
})

export async function salvarRegras(dados: Partial<ValoresRegras>): Promise<Regras> {
  return regrasSchema.parse(await enviarJson('/api/escola/regras/', 'PATCH', dados))
}
