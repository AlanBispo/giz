import { z } from 'zod'

export const tipoSchema = z.enum(['atividade', 'prova'])

export const publicacaoSchema = z.object({
  id: z.number().int(),
  versao: z.number().int(),
  titulo: z.string(),
  descricao: z.string(),
  data: z.iso.date(),
  tipo: tipoSchema,
  valor: z.string(),
  turma: z.number().int(),
  disciplina: z.number().int(),
  bimestre: z.number().int(),
  nome_turma: z.string(),
  nome_disciplina: z.string(),
  numero_bimestre: z.number().int(),
})

export const vinculoSchema = z.object({
  turma: z.number().int(),
  disciplina: z.number().int(),
  nome_turma: z.string(),
  nome_disciplina: z.string(),
  bimestres: z.array(z.object({ id: z.number().int(), numero: z.number().int() })),
})

export const saldoSchema = z.object({ saldo: z.string(), pontos_prova: z.string() })

export type Publicacao = z.infer<typeof publicacaoSchema>
export type Vinculo = z.infer<typeof vinculoSchema>
export type Periodo = Pick<Publicacao, 'turma' | 'disciplina' | 'bimestre'>
export type DadosPublicacao = Periodo & Pick<Publicacao, 'titulo' | 'descricao' | 'data' | 'tipo'>
  & { valor?: string; versao?: number }
