# [WORKFLOW CI]

## 1. CONTEXTO
Plataforma: GitHub Actions
Objetivo: validar PRs de código gerado com Codex

## 2. INSTRUÇÕES
- [ ] Executar build
- [ ] Executar testes
- [ ] Executar lint e type-check
- [ ] Publicar logs úteis em falha

## 3. TAREFA
Criar workflow para validar [módulo/projeto].

## 4. SAÍDA ESPERADA
```yaml
name: CI
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
```
