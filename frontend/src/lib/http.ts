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
  metodo: 'POST' | 'PATCH',
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
