import { useSair } from '../hooks/useSessao'
import { perfis, type Usuario } from '../types'

export function Inicio({ usuario }: { usuario: Usuario }) {
  const sair = useSair()

  return (
    <>
      <h1>Olá, {usuario.nome}</h1>
      <p>{perfis[usuario.perfil]}</p>
      <button type="button" onClick={() => sair.mutate()} disabled={sair.isPending}>
        {sair.isPending ? 'Saindo…' : 'Sair'}
      </button>
      {sair.isError && <p role="alert">Não foi possível sair. Tente novamente.</p>}
    </>
  )
}
