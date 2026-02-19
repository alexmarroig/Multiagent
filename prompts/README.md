# Biblioteca de Prompts Codex para AgentOS

Este diretório centraliza templates para acelerar a criação de prompts de engenharia de software para o fluxo Claude → Codex no AgentOS.

## Estrutura

- `frontend/`: templates para componentes, páginas, hooks e formulários.
- `backend/`: templates para endpoints, schemas, tools e integrações.
- `infra/`: templates para Docker, CI e deploy.
- `examples/`: exemplos few-shot completos.

## Como usar

1. Escolha um template por tipo de tarefa.
2. Preencha os campos entre colchetes (`[CAMPO]`) com o contexto real.
3. Garanta que as seções CONTEXTO / INSTRUÇÕES / TAREFA / SAÍDA ESPERADA estejam completas.
4. Execute o checklist final antes de enviar para o Codex.

## Checklist rápido

- [ ] 8 seções preenchidas
- [ ] >= 2 exemplos few-shot
- [ ] >= 3 testes mínimos definidos
- [ ] Critérios de sucesso mensuráveis
- [ ] Estrutura de arquivos clara
- [ ] Dependências com versões
- [ ] Estratégia de validação pré-commit
