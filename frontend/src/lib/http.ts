export async function obterJson(caminho: string): Promise<unknown> {
  const resposta = await fetch(caminho)

  if (!resposta.ok) {
    throw new Error(`Falha na API (HTTP ${resposta.status}).`)
  }

  return resposta.json()
}
