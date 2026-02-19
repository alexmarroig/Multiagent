# 🎯 Sistema Master de Prompt Engineering para AgentOS

Este documento consolida um contrato padrão para criação de prompts que maximizam a chance de o Codex entregar código funcional, testável e pronto para produção na primeira iteração.

## Objetivo
Gerar prompts estruturados com 4 blocos obrigatórios (CONTEXTO / INSTRUÇÕES / TAREFA / SAÍDA ESPERADA), critérios mensuráveis e validação automatizável.

## Regras de ouro
1. Estruturar o prompt em seções claras.
2. Incluir exemplos concretos (few-shot).
3. Definir critérios de sucesso mensuráveis.
4. Especificar testes mínimos.
5. Explicitar estrutura de arquivos esperada.
6. Definir padrões de qualidade (tipagem, lint, error handling).

## Artefatos relacionados
- Biblioteca de templates: `prompts/`
- Script de validação: `validate_codex_output.sh`
- CI para PRs: `.github/workflows/codex-validation.yml`

## Uso recomendado
1. Escolha um template em `prompts/`.
2. Preencha o contexto do módulo e requisitos funcionais/não-funcionais.
3. Adicione ao menos 2 exemplos few-shot.
4. Defina no mínimo 3 testes obrigatórios.
5. Execute checklist pré-commit.
