import { enviarJson, ErroHttp, obterJson } from '../../../lib/http'
import { type Credenciais, type Usuario, usuarioSchema } from '../types'

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
  return usuarioSchema.parse(await enviarJson('/api/login/', 'POST', credenciais))
}

export async function sair(): Promise<void> {
  await enviarJson('/api/logout/', 'POST')
}
