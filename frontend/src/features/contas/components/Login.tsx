import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { ErroHttp } from '../../../lib/http'
import { useEntrar } from '../hooks/useSessao'
import { type Credenciais, credenciaisSchema } from '../types'

export function Login() {
  const entrar = useEntrar()
  const {
    register,
    handleSubmit,
    resetField,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Credenciais>({
    resolver: zodResolver(credenciaisSchema),
  })

  async function enviar(dados: Credenciais) {
    try {
      await entrar(dados)
    } catch (erro) {
      resetField('senha')
      const status = erro instanceof ErroHttp ? erro.status : undefined
      const mensagens: Record<number, string> = {
        400: 'E-mail ou senha inválidos.',
        429: 'Muitas tentativas. Aguarde e tente novamente.',
      }
      setError('root', {
        message: (status && mensagens[status]) || 'Não foi possível entrar. Tente novamente.',
      })
    }
  }

  return (
    <>
      <h1>Entrar no Giz</h1>
      <form noValidate onSubmit={handleSubmit(enviar)}>
        <label>
          E-mail
          <input
            type="text"
            inputMode="email"
            autoComplete="username"
            aria-invalid={Boolean(errors.email)}
            aria-describedby={errors.email ? 'erro-email' : undefined}
            {...register('email')}
          />
        </label>
        {errors.email && <p id="erro-email" role="alert">{errors.email.message}</p>}
        <label>
          Senha
          <input
            type="password"
            autoComplete="current-password"
            aria-invalid={Boolean(errors.senha)}
            aria-describedby={errors.senha ? 'erro-senha' : undefined}
            {...register('senha')}
          />
        </label>
        {errors.senha && <p id="erro-senha" role="alert">{errors.senha.message}</p>}
        {errors.root && <p role="alert">{errors.root.message}</p>}
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </>
  )
}
