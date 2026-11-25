import { queryOptions } from '@tanstack/react-query'
import { z } from 'zod'

import { enviarJson, ErroHttp, obterJson } from '../../../lib/http'

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

const errosSchema = z.record(z.string(), z.union([z.string(), z.array(z.string())]))

export function mensagemDeErro(erro: unknown, rotulos: Record<string, string>): string {
  if (erro instanceof ErroHttp && erro.status === 400) {
    const resposta = errosSchema.safeParse(erro.detalhes)
    if (resposta.success) {
      return Object.entries(resposta.data).map(([chave, valor]) => {
        const mensagem = Array.isArray(valor) ? valor.join(' ') : valor
        return rotulos[chave] ? `${rotulos[chave]} — ${mensagem}` : mensagem
      }).join(' ')
    }
  }
  return 'Não foi possível salvar. Confira sua conexão e tente novamente.'
}
