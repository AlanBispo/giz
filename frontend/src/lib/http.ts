import { z } from 'zod'

export class ErroHttp extends Error {
  constructor(public readonly status: number, public readonly detalhes?: unknown) {
    super(`Falha na API (HTTP ${status}).`)
  }
}

async function requisitar(caminho: string, opcoes?: RequestInit): Promise<Response> {
  const resposta = await fetch(caminho, opcoes)

  if (!resposta.ok) {
    throw new ErroHttp(resposta.status, await resposta.json().catch(() => undefined))
  }

  return resposta
}

export async function obterJson(caminho: string, signal?: AbortSignal): Promise<unknown> {
  const resposta = await requisitar(caminho, { signal })
  return resposta.json()
}

export async function enviarJson(
  caminho: string,
  metodo: 'POST' | 'PATCH' | 'DELETE',
  dados?: object,
): Promise<unknown> {
  const token = z.object({ csrfToken: z.string() }).parse(await obterJson('/api/csrf/'))
  const resposta = await requisitar(caminho, {
    method: metodo,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': token.csrfToken,
    },
    body: JSON.stringify(dados),
  })
  return resposta.status === 204 ? undefined : resposta.json()
}

const errosSchema = z.record(z.string(), z.union([z.string(), z.array(z.string())]))

export function mensagemDeErro(erro: unknown, rotulos: Record<string, string> = {}): string {
  if (erro instanceof ErroHttp && (erro.status === 400 || erro.status === 409)) {
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
