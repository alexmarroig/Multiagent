# [NOME DA FEATURE UI]

## 1. CONTEXTO
Projeto: AgentOS Frontend
Stack: Next.js 14 + TypeScript + TailwindCSS + shadcn/ui
Módulo: [Admin / Canvas / Auth / etc]

## 2. INSTRUÇÕES
### 2.1 Requisitos Funcionais
- [ ] Renderiza em dark mode
- [ ] Estados loading/success/error
- [ ] Acessível (ARIA)
- [ ] Responsivo (mobile-first)

### 2.2 Estrutura Esperada
```text
components/
├── [ComponentName].tsx
├── [ComponentName].test.tsx
└── types.ts
```

### 2.3 Interface
```ts
interface [ComponentName]Props {
  [prop1]: [tipo]
  [prop2]?: [tipo]
  onAction: (data: [tipo]) => void
}
```

## 3. TAREFA
Implemente o componente [Nome] com integração em [API/store/context].

## 4. SAÍDA ESPERADA
- Código TypeScript estrito
- 3+ testes com React Testing Library
- Sem warnings de lint
