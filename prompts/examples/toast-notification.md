# Exemplo Few-Shot 1: Toast Notification Component

## Input
"Preciso de um componente Toast com tipos success/error/warning/info e auto-dismiss em 5s."

## Output (resumo)
- Estrutura esperada: `Toast.tsx`, `ToastContainer.tsx`, `useToast.ts`, `Toast.test.tsx`
- Requisitos: posição top-right, animação entrada/saída, acessibilidade, suporte a múltiplos toasts
- Testes mínimos:
  1. renderiza mensagem
  2. fecha automaticamente
  3. fecha ao clicar no botão
