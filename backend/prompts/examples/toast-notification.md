# Exemplo Prático 1: Componente Toast

## Input (pedido)
```text
Preciso de um componente Toast de notificação para o AgentOS.
Deve suportar 4 tipos: success, error, warning, info.
Deve aparecer no canto superior direito e desaparecer após 5s.
```

## Output esperado (resumo do prompt final)
- Definir contexto: Next.js 14 + TypeScript + Tailwind + Framer Motion
- Estrutura de arquivos:
  - `components/ui/Toast.tsx`
  - `components/ui/ToastContainer.tsx`
  - `components/ui/useToast.ts`
  - `components/ui/Toast.test.tsx`
- Requisitos: auto-dismiss, fechar manual, acessibilidade, múltiplos toasts
- Testes mínimos:
  1. renderiza mensagem
  2. fecha após duração
  3. fecha no clique do botão
