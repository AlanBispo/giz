import { z } from 'zod'

export const senhaSchema = z.string()
  .refine((senha) => [...senha].length <= 4096, 'Senha muito longa.')
