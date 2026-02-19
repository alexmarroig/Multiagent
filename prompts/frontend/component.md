# [NOME DA FEATURE UI]

## 1. CONTEXTO
Projeto: AgentOS Frontend
Stack: Next.js 14 + TypeScript + TailwindCSS + shadcn/ui
Módulo: [Admin / Canvas / Auth / etc]

## 2. INSTRUÇÕES

### 2.1 Requisitos Funcionais
- [ ] Componente renderiza corretamente em dark mode
- [ ] Suporta estados: loading, success, error
- [ ] Acessibilidade (ARIA labels)
- [ ] Responsivo (mobile-first)

### 2.2 Estrutura Esperada
```text
components/
├── [ComponentName].tsx       ← Componente principal
├── [ComponentName].test.tsx  ← Testes com React Testing Library
└── types.ts                  ← Tipos TypeScript
```

### 2.3 Interface do Componente
```typescript
interface [ComponentName]Props {
  [prop1]: [tipo]
  [prop2]?: [tipo]
  onAction: (data: [tipo]) => void
}
```

## 3. TAREFA
Implemente o componente [Nome] que [descrição detalhada].

Deve:
- Usar hooks: useState, useEffect, [outros]
- Integrar com [API/store/context]
- Exibir feedback visual de loading/erro
- Ter pelo menos 3 testes unitários

## 4. SAÍDA ESPERADA

### Código
```typescript
export function [ComponentName](props: [ComponentName]Props) {
  return <section>[UI]</section>
}
```

### Testes
```typescript
test('renderiza estado inicial corretamente', () => {
  render(<[ComponentName] {...props} />)
  expect(screen.getByText('[texto]')).toBeInTheDocument()
})
```

## 5. VALIDAÇÃO
- [ ] `npm run dev`
- [ ] Dark mode funciona
- [ ] Testes passam
- [ ] Sem warnings no console
