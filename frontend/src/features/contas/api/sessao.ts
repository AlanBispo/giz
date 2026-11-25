import { z } from 'zod'

import { enviarPost, ErroHttp, obterJson } from '../../../lib/http'
import { type Credenciais, type Usuario, usuarioSchema } from '../types'

async function obterTokenCsrf(): Promise<string> {
  const dados = await obterJson('/api/csrf/')
  return z.object({ csrfToken: z.string() }).parse(dados).csrfToken
}

export async function consultarSessao(signal: AbortSignal): Promise<Usuario | null> {
  try {
    return usuarioSchema.parse(await obterJson('/api/me/', signal))
  } catch (erro) {
    if (erro instanceof ErroHttp && erro.status === 403) {
      return null
    }
    throw erro
  }
}

export async function entrar(credenciais: Credenciais): Promise<Usuario> {
  const token = await obterTokenCsrf()
  return usuarioSchema.parse(await enviarPost('/api/login/', token, credenciais))
}

export async function sair(): Promise<void> {
  const token = await obterTokenCsrf()
  await enviarPost('/api/logout/', token)
}
