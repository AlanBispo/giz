import { z } from 'zod'

export const turmasSchema = z.array(z.object({
  id: z.number().int(),
  nome: z.string(),
  ano: z.number().int(),
}))

const linhaSchema = z.object({
  matricula: z.number().int(),
  aluno: z.string(),
  turma: z.string(),
  ano: z.number().int(),
  disciplina: z.string(),
  bimestre: z.number().int(),
  atividades: z.string().nullable(),
  prova: z.string().nullable(),
  nota: z.string(),
  situacao: z.enum(['aprovado', 'abaixo_da_media']),
})

export const boletimSchema = z.object({
  media_minima: z.string(),
  linhas: z.array(linhaSchema),
})
