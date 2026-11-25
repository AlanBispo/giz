import { z } from 'zod'

import { senhaSchema } from '../../lib/validacao'

const perfilSchema = z.enum(['aluno', 'professor', 'coordenacao', 'diretoria'])

export const perfis = {
  aluno: 'Aluno',
  professor: 'Professor',
  coordenacao: 'Coordenação',
  diretoria: 'Diretoria',
} satisfies Record<z.infer<typeof perfilSchema>, string>

export const usuarioSchema = z.object({
  id: z.number().int(),
  nome: z.string(),
  email: z.string(),
  perfil: perfilSchema,
})

export const credenciaisSchema = z.object({
  email: z.string().trim().min(1, 'Informe seu e-mail.')
    .refine((email) => [...email].length <= 254, 'O e-mail é muito longo.'),
  senha: senhaSchema.refine((senha) => senha.length > 0, 'Informe sua senha.'),
})

export type Usuario = z.infer<typeof usuarioSchema>
export type Credenciais = z.infer<typeof credenciaisSchema>
