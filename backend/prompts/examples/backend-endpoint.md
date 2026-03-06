# Exemplo Prático 2: Endpoint autenticado

## Input (pedido)
```text
Criar endpoint POST /api/flows/execute com JWT, validação de input e logs.
```

## Output esperado (resumo do prompt final)
- Endpoint com `Depends(get_current_user)`
- Schemas Pydantic (`FlowExecuteRequest`, `FlowExecuteResponse`)
- Tratamento de erro para 400/401/500
- Estrutura alvo:
  - `backend/api/routes_flows.py`
  - `backend/api/schemas.py`
  - `backend/tests/test_flows_execute.py`
- Testes mínimos:
  1. sucesso autenticado
  2. falha sem token
  3. input inválido
  4. erro interno controlado
