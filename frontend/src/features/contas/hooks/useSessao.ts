import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { consultarSessao, entrar, sair } from '../api/sessao'
import type { Credenciais, Usuario } from '../types'

const chaveSessao = ['sessao'] as const

export function useSessao() {
  return useQuery({
    queryKey: chaveSessao,
    queryFn: ({ signal }) => consultarSessao(signal),
    retry: false,
    networkMode: 'always',
  })
}

function useAtualizarSessao() {
  const queryClient = useQueryClient()

  return async (usuario: Usuario | null) => {
    await queryClient.cancelQueries({ queryKey: chaveSessao })
    queryClient.setQueryData(chaveSessao, usuario)
  }
}

export function useEntrar() {
  const atualizarSessao = useAtualizarSessao()
  const { mutateAsync, reset } = useMutation({
    mutationFn: entrar,
    onSuccess: atualizarSessao,
    gcTime: 0,
    networkMode: 'always',
  })

  return async (credenciais: Credenciais) => {
    try {
      await mutateAsync(credenciais)
    } finally {
      reset()
    }
  }
}

export function useSair() {
  const atualizarSessao = useAtualizarSessao()

  return useMutation({
    mutationFn: sair,
    onSuccess: () => atualizarSessao(null),
    networkMode: 'always',
  })
}
