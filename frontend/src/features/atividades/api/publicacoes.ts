import { queryOptions, type QueryClient } from '@tanstack/react-query'
import { z } from 'zod'

import { enviarJson, obterJson } from '../../../lib/http'
import {
  type DadosPublicacao, type Periodo, publicacaoSchema, saldoSchema, vinculoSchema,
} from '../types'

const base = '/api/atividades/'

function chavePublicacoes(usuario: number) {
  return ['publicacoes', usuario] as const
}

export async function recarregarPublicacoes(queryClient: QueryClient, usuario: number): Promise<void> {
  const filtro = { queryKey: chavePublicacoes(usuario) }
  await queryClient.cancelQueries(filtro)
  await queryClient.invalidateQueries(filtro)
}

export function consultaPublicacoes(usuario: number) {
  return queryOptions({
    queryKey: [...chavePublicacoes(usuario), 'lista'],
    queryFn: async ({ signal }) => z.array(publicacaoSchema).parse(await obterJson(base, signal)),
    networkMode: 'always',
    retry: false,
    gcTime: 0,
  })
}

export function consultaVinculos(usuario: number, professor: boolean) {
  return queryOptions({
    queryKey: [...chavePublicacoes(usuario), 'contexto'],
    queryFn: async ({ signal }) => z.array(vinculoSchema).parse(await obterJson(`${base}contexto/`, signal)),
    enabled: professor,
    networkMode: 'always',
    retry: false,
    gcTime: 0,
  })
}

export function consultaSaldo(usuario: number, periodo: Periodo | null) {
  return queryOptions({
    queryKey: [...chavePublicacoes(usuario), 'saldo', periodo],
    queryFn: async ({ signal }) => {
      if (!periodo) throw new Error('Selecione turma, disciplina e bimestre.')
      const parametros = new URLSearchParams({
        turma: String(periodo.turma),
        disciplina: String(periodo.disciplina),
        bimestre: String(periodo.bimestre),
      })
      return saldoSchema.parse(await obterJson(`${base}saldo/?${parametros}`, signal))
    },
    enabled: periodo !== null,
    networkMode: 'always',
    retry: false,
    gcTime: 0,
  })
}

export async function salvarPublicacao(dados: DadosPublicacao, id?: number): Promise<void> {
  await enviarJson(id === undefined ? base : `${base}${id}/`, id === undefined ? 'POST' : 'PATCH', dados)
}

export async function excluirPublicacao({ id, versao }: { id: number; versao: number }): Promise<void> {
  await enviarJson(`${base}${id}/`, 'DELETE', { versao })
}
