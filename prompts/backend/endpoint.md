# [NOME DO ENDPOINT]

## 1. CONTEXTO
Projeto: AgentOS Backend
Stack: FastAPI + Pydantic + Supabase
Módulo: [Auth / Agents / Flows / Tools]

## 2. INSTRUÇÕES
- [ ] Auth JWT com `Depends(get_current_user)`
- [ ] Input validado por Pydantic
- [ ] Retorno 200/400/401 conforme cenário
- [ ] Logs de requisição

## 3. TAREFA
Implementar `[MÉTODO] /api/[caminho]` com validações e tratamento de erro.

## 4. SAÍDA ESPERADA
```py
@router.[metodo]("/[caminho]")
async def [funcao](request: [RequestModel], user=Depends(get_current_user)):
    ...
```
