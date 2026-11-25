import { z } from 'zod'

const publicacaoSchema = z.object({
  id: z.number().int(),
  titulo: z.string(),
  tipo: z.enum(['atividade', 'prova']),
  data: z.iso.date(),
  valor: z.string(),
  versao: z.number().int(),
  nome_turma: z.string(),
  nome_disciplina: z.string(),
  numero_bimestre: z.number().int(),
})

export const lancamentoSchema = z.object({
  publicacao: publicacaoSchema,
  alunos: z.array(z.object({
    matricula: z.number().int(),
    nome: z.string(),
    valor: z.string().nullable(),
  })),
})

export const notasSchema = z.array(z.object({
  id: z.number().int(),
  aluno: z.string(),
  matricula: z.number().int(),
  publicacao: publicacaoSchema,
  valor: z.string(),
}))

export type Lancamento = z.infer<typeof lancamentoSchema>
export type NotaInformada = { matricula: number; valor: string }
