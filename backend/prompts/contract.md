# [NOME DA FEATURE/MÓDULO]

## 1. CONTEXTO
**Projeto:** AgentOS v[versão]
**Módulo:** [Frontend / Backend / Infraestrutura]
**Stack atual:**
- [lista de tecnologias já em uso]

**Estado do projeto:**
- [o que já existe e funciona]
- [últimos commits relevantes]

**Objetivo de negócio:**
[Por que essa feature é necessária? Qual problema resolve?]

---

## 2. INSTRUÇÕES

### 2.1 Requisitos Funcionais
- [ ] [Requisito 1 — mensurável]
- [ ] [Requisito 2 — mensurável]
- [ ] [Requisito N]

### 2.2 Requisitos Não-Funcionais
- Performance: [critério]
- Segurança: [critério]
- Qualidade: [padrões de código]

### 2.3 Dependências
**Bibliotecas a usar:**
- [lib1@versão] — [justificativa]
- [lib2@versão] — [justificativa]

**NÃO usar:**
- [lib bloqueada] — [razão]

### 2.4 Padrões de Código
- TypeScript com tipos explícitos
- Funções < 50 linhas
- Error handling com try/catch
- Comentários em português nas partes complexas
- Imports ordenados alfabeticamente

---

## 3. TAREFA

### 3.1 Estrutura de Arquivos Esperada
```text
[caminho]/
├── [arquivo1.ts]
├── [arquivo2.tsx]
└── [arquivo3.test.ts]
```

### 3.2 Funções/Componentes Principais
1. **[NomeFunção1]**
   - Input: [tipo]
   - Output: [tipo]
   - Responsabilidade: [descrição]

2. **[ComponenteX]**
   - Props: [interface]
   - Estado: [descrição]
   - Renderiza: [descrição]

### 3.3 Casos de Uso a Cobrir
- ✅ Caso feliz
- ⚠️ Erro esperado
- 🔒 Edge case

---

## 4. SAÍDA ESPERADA

### 4.1 Formato
```typescript
export interface [Interface] {
  [campo]: [tipo]
}

export function [funcao]([params]): [retorno] {
  // implementação
}
```

### 4.2 Testes Mínimos (deve passar)
```typescript
describe('[Feature]', () => {
  test('[cenário 1]', () => {
    expect([resultado]).toBe([esperado])
  })
})
```

### 4.3 Critérios de Sucesso
- [ ] Código compila sem erros
- [ ] Testes passam
- [ ] Lint passa (ESLint/Ruff)
- [ ] TypeScript strict mode habilitado
- [ ] Documentação inline presente

---

## 5. VALIDAÇÃO
### 5.1 Checklist Pré-Commit
- [ ] `npm run build`
- [ ] `npm test`
- [ ] `npm run lint`
- [ ] `npm run type-check`

### 5.2 Teste Manual
1. [Passo 1]
2. [Passo 2]
3. [Passo N]

---

## 6. EXEMPLOS (Few-Shot)
### Exemplo de Input
```text
[exemplo de chamada/uso]
```

### Exemplo de Output
```text
[exemplo de resultado esperado]
```

---

## 7. CONTEXTO ADICIONAL
### 7.1 Decisões arquiteturais
### 7.2 Alternativas consideradas

---

## 8. PRÓXIMOS PASSOS
1. [Integração]
2. [E2E]
3. [Deploy]
