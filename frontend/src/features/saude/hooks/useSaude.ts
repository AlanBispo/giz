import { useQuery } from '@tanstack/react-query'

import { consultarSaude } from '../api/consultarSaude'

export function useSaude() {
  return useQuery({ queryKey: ['saude'], queryFn: consultarSaude, retry: false })
}
