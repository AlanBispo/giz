import { obterJson } from '../../../lib/http'

export async function consultarSaude() {
  const dados = await obterJson('/api/saude/')

  if (typeof dados !== 'object' || dados === null || !('status' in dados) || dados.status !== 'ok') {
    throw new Error('Resposta inesperada da API de saúde.')
  }

  return dados.status
}
