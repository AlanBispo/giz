import { useSaude } from '../hooks/useSaude'

export function EstadoDaApi() {
  const saude = useSaude()

  return (
    <p role="status">
      {saude.isPending && 'Verificando a conexão com a API…'}
      {saude.isError && 'API ou banco de dados indisponível.'}
      {saude.isSuccess && `API e banco de dados operacionais (${saude.data}).`}
    </p>
  )
}
