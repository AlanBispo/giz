import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { mensagemDeErro } from '../../../lib/http'
import { cadastrar, consultaCadastro, type Recurso } from '../api/escola'
import { cadastros } from '../cadastros'

export function Cadastro({ recurso }: { recurso: Recurso }) {
  const config = cadastros[recurso]
  const lista = useQuery(consultaCadastro(recurso))
  const queryClient = useQueryClient()
  const fontes = [...new Set(config.campos.flatMap(({ fonte }) => fonte ? [fonte.recurso] : []))]
  const consultas = useQueries({ queries: fontes.map(consultaCadastro) })
  const schema = z.object(Object.fromEntries(config.campos.map(({ nome, validar }) => [nome, validar])))
  const { register, handleSubmit, reset, resetField, setError, formState: { errors, isSubmitting } } =
    useForm<Record<string, string>>({ resolver: zodResolver(schema) })
  const gravar = useMutation({
    mutationFn: (dados: Record<string, string>) => cadastrar(recurso, dados),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: consultaCadastro(recurso).queryKey }),
    networkMode: 'always',
    gcTime: 0,
  })
  const opcoes = config.campos.map(({ opcoes, fonte }) => {
    if (!fonte) return opcoes

    const registros = consultas[fontes.indexOf(fonte.recurso)]?.data ?? []
    return registros
      .filter((registro) => !fonte.perfil || registro.perfil === fonte.perfil)
      .map((registro) => ({ valor: String(registro.id), rotulo: fonte.rotulo(registro) }))
  })
  const faltaOpcao = opcoes.some((valores) => valores?.length === 0)

  async function enviar(dados: Record<string, string>) {
    try {
      await gravar.mutateAsync(dados)
      reset()
    } catch (erro) {
      if (recurso === 'pessoas') resetField('senha')
      const rotulos = Object.fromEntries(config.campos.map(({ nome, rotulo }) => [nome, rotulo]))
      setError('root', { message: mensagemDeErro(erro, rotulos) })
    } finally {
      gravar.reset()
    }
  }

  return (
    <section>
      <h2>{config.titulo}</h2>
      <div className="cadastro-escolar">
        <div className="tabela-escolar">
          {lista.isPending && <p role="status">Carregando cadastros…</p>}
          {lista.isError && (
            <>
              <p role="alert">Não foi possível carregar os cadastros.</p>
              <button type="button" onClick={() => void lista.refetch()}>Tentar novamente</button>
            </>
          )}
          {lista.data?.length === 0 && <p>Nenhum cadastro encontrado.</p>}
          {lista.data && lista.data.length > 0 && (
            <table aria-label={config.titulo}>
              <thead>
                <tr>{config.colunas.map(({ nome, rotulo }) => <th key={nome} scope="col">{rotulo}</th>)}</tr>
              </thead>
              <tbody>
                {lista.data.map((registro) => (
                  <tr key={registro.id}>
                    {config.colunas.map(({ nome, exibir }) => (
                      <td key={nome}>{exibir ? exibir(registro) : registro[nome]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div>
          <h3>Novo cadastro</h3>
          {consultas.some((consulta) => consulta.isError) && (
            <>
              <p role="alert">Não foi possível carregar as opções do formulário.</p>
              <button type="button" onClick={() => {
                void Promise.all(consultas.filter((consulta) => consulta.isError).map((consulta) => consulta.refetch()))
              }}>Recarregar opções</button>
            </>
          )}
          <form noValidate onSubmit={handleSubmit(enviar)}>
            {config.campos.map((campo, index) => {
              const valores = opcoes[index]
              const erro = errors[campo.nome]
              const atributos = {
                ...register(campo.nome),
                disabled: isSubmitting,
                'aria-invalid': Boolean(erro),
                'aria-describedby': erro ? `erro-${campo.nome}` : undefined,
              }
              return (
                <label key={campo.nome}>
                  {campo.rotulo}
                  {valores ? (
                    <select defaultValue="" {...atributos}>
                      <option value="">{valores.length ? 'Selecione' : 'Nenhuma opção disponível'}</option>
                      {valores.map(({ valor, rotulo }) => <option key={valor} value={valor}>{rotulo}</option>)}
                    </select>
                  ) : (
                    <input
                      {...atributos}
                      type={campo.tipo ?? 'text'}
                      inputMode={campo.inputMode}
                      autoComplete={campo.tipo === 'password' ? 'new-password' : undefined}
                    />
                  )}
                  {erro && <span id={`erro-${campo.nome}`} role="alert">{erro.message}</span>}
                </label>
              )
            })}
            {errors.root && <p role="alert">{errors.root.message}</p>}
            <button type="submit" disabled={isSubmitting || faltaOpcao}>
              {isSubmitting ? 'Salvando…' : 'Cadastrar'}
            </button>
          </form>
        </div>
      </div>
    </section>
  )
}
