# Biblioteca de Prompts Prontos (AgentOS)

Coleção de templates para acelerar pedidos ao Codex com padrão de qualidade consistente.

## Estrutura

```text
prompts/
├── contract.md
├── system-prompt.md
├── frontend/
│   ├── component.md
│   ├── form.md
│   ├── hook.md
│   └── page.md
├── backend/
│   ├── endpoint.md
│   ├── integration.md
│   ├── schema.md
│   └── tool.md
├── infra/
│   ├── ci.md
│   ├── deploy.md
│   └── docker.md
└── examples/
    ├── backend-endpoint.md
    └── toast-notification.md
```

## Regras de uso

1. Sempre use **CONTEXTO / INSTRUÇÕES / TAREFA / SAÍDA ESPERADA**.
2. Complete as 8 seções quando usar `contract.md`.
3. Inclua no mínimo **2 few-shots** e **3 testes mínimos**.
4. Defina critérios objetivos para build, lint, testes e type-check.
5. Antes de enviar ao Codex, revise com o checklist final.
