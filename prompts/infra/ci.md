# [WORKFLOW CI]

## 1. CONTEXTO
Plataforma: GitHub Actions

## 2. INSTRUÇÕES
- [ ] Executar build
- [ ] Executar testes
- [ ] Executar lint e type-check
- [ ] Falhar com logs úteis

## 3. TAREFA
Criar workflow para validar PRs em [módulo].

## 4. SAÍDA ESPERADA
```yaml
name: CI
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
```
