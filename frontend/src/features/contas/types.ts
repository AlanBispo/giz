import { z } from 'zod'

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
  email: z.string().trim().min(1, 'Informe seu e-mail.').max(254, 'O e-mail é muito longo.'),
  senha: z.string().min(1, 'Informe sua senha.').max(4096),
})

export type Usuario = z.infer<typeof usuarioSchema>
export type Credenciais = z.infer<typeof credenciaisSchema>
