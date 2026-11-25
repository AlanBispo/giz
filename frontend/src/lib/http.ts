export class ErroHttp extends Error {
  constructor(public readonly status: number) {
    super(`Falha na API (HTTP ${status}).`)
  }
}

async function requisitar(caminho: string, opcoes?: RequestInit): Promise<Response> {
  const resposta = await fetch(caminho, opcoes)

  if (!resposta.ok) {
    throw new ErroHttp(resposta.status)
  }

  return resposta
}

export async function obterJson(caminho: string, signal?: AbortSignal): Promise<unknown> {
  const resposta = await requisitar(caminho, { signal })
  return resposta.json()
}

export async function enviarPost(
  caminho: string,
  csrfToken: string,
  dados?: object,
): Promise<unknown> {
  const resposta = await requisitar(caminho, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(dados),
  })
  return resposta.status === 204 ? undefined : resposta.json()
}
