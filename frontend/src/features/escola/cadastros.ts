import { z } from 'zod'

import { senhaSchema } from '../../lib/validacao'
import type { Recurso, Registro } from './api/escola'

export type Opcao = { valor: string; rotulo: string }

export type Campo = {
  nome: string
  rotulo: string
  tipo?: 'text' | 'password' | 'number'
  inputMode?: 'email' | 'numeric'
  validar: z.ZodType<string, string>
  opcoes?: Opcao[]
  fonte?: {
    recurso: Recurso
    rotulo: (registro: Registro) => string
    perfil?: 'aluno' | 'professor'
  }
}

type Coluna = {
  nome: string
  rotulo: string
  exibir?: (registro: Registro) => string
}

type Cadastro = { titulo: string; campos: Campo[]; colunas: Coluna[] }

const texto = (limite: number) => z.string().trim()
  .min(1, 'Campo obrigatório.')
  .refine((valor) => [...valor].length <= limite, `Use até ${limite} caracteres.`)
const id = z.string().regex(/^[1-9]\d*$/, 'Selecione uma opção.')

const campoAno: Campo = {
  nome: 'ano_letivo', rotulo: 'Ano letivo', validar: id,
  fonte: { recurso: 'anos-letivos', rotulo: (registro) => String(registro.ano) },
}

const campoTurma: Campo = {
  nome: 'turma', rotulo: 'Turma', validar: id,
  fonte: { recurso: 'turmas', rotulo: (registro) => `${registro.nome} (${registro.ano})` },
}

function campoPessoa(perfil: 'professor' | 'aluno', rotulo: string): Campo {
  return {
    nome: perfil, rotulo, validar: id,
    fonte: {
      recurso: 'pessoas', perfil, rotulo: (registro) => `${registro.nome} — ${registro.email}`,
    },
  }
}

const colunaAno = { nome: 'ano', rotulo: 'Ano letivo' }
const colunaNome = { nome: 'nome', rotulo: 'Nome' }

export const cadastros: Record<Recurso, Cadastro> = {
  pessoas: {
    titulo: 'Professores e alunos',
    campos: [
      { ...colunaNome, validar: texto(150) },
      { nome: 'email', rotulo: 'E-mail', inputMode: 'email', validar: texto(254) },
      {
        nome: 'perfil', rotulo: 'Perfil',
        validar: z.enum(['professor', 'aluno'], 'Selecione um perfil.'),
        opcoes: [{ valor: 'professor', rotulo: 'Professor' }, { valor: 'aluno', rotulo: 'Aluno' }],
      },
      {
        nome: 'senha', rotulo: 'Senha inicial', tipo: 'password',
        validar: senhaSchema
          .refine((senha) => [...senha.trim()].length >= 8, 'Use pelo menos 8 caracteres.'),
      },
    ],
    colunas: [
      colunaNome,
      { nome: 'email', rotulo: 'E-mail' },
      { nome: 'perfil', rotulo: 'Perfil', exibir: ({ perfil }) => perfil === 'professor' ? 'Professor' : 'Aluno' },
    ],
  },
  'anos-letivos': {
    titulo: 'Anos letivos',
    campos: [{
      ...colunaAno, tipo: 'number', inputMode: 'numeric',
      validar: z.string().regex(/^[1-9]\d{0,3}$/, 'Informe um ano entre 1 e 9999.'),
    }],
    colunas: [colunaAno],
  },
  bimestres: {
    titulo: 'Bimestres',
    campos: [
      campoAno,
      {
        nome: 'numero', rotulo: 'Bimestre', validar: z.enum(['1', '2', '3', '4'], 'Selecione o bimestre.'),
        opcoes: [1, 2, 3, 4].map((numero) => ({ valor: String(numero), rotulo: `${numero}º` })),
      },
    ],
    colunas: [colunaAno, { nome: 'numero', rotulo: 'Bimestre', exibir: ({ numero }) => `${numero}º` }],
  },
  turmas: {
    titulo: 'Turmas',
    campos: [{ ...colunaNome, validar: texto(100) }, campoAno],
    colunas: [colunaNome, colunaAno],
  },
  disciplinas: {
    titulo: 'Disciplinas',
    campos: [{ ...colunaNome, validar: texto(100) }],
    colunas: [colunaNome],
  },
  vinculos: {
    titulo: 'Vínculos docentes',
    campos: [
      campoPessoa('professor', 'Professor'),
      campoTurma,
      {
        nome: 'disciplina', rotulo: 'Disciplina', validar: id,
        fonte: { recurso: 'disciplinas', rotulo: (registro) => String(registro.nome) },
      },
    ],
    colunas: [
      { nome: 'nome_professor', rotulo: 'Professor' },
      { nome: 'nome_turma', rotulo: 'Turma' },
      { nome: 'nome_disciplina', rotulo: 'Disciplina' },
    ],
  },
  matriculas: {
    titulo: 'Matrículas',
    campos: [campoPessoa('aluno', 'Aluno'), campoTurma],
    colunas: [{ nome: 'nome_aluno', rotulo: 'Aluno' }, { nome: 'nome_turma', rotulo: 'Turma' }],
  },
}
