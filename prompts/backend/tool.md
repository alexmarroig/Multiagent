# [NOME DA TOOL]

## 1. CONTEXTO
Projeto: AgentOS Backend
Arquivo alvo: `backend/tools/[nome]_tools.py`

## 2. INSTRUÇÕES
- [ ] Usar decorator `@tool`
- [ ] Timeout de 30s
- [ ] Retry (3 tentativas)
- [ ] Error handling claro
- [ ] Retorno serializável

## 3. TAREFA
Implementar tool para [funcionalidade] com integração a [serviço].

## 4. SAÍDA ESPERADA
```python
from crewai.tools import tool

@tool("[nome_tool]")
def [funcao_tool]([params]) -> str:
    ...
```
