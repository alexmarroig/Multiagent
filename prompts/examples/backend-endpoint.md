# Exemplo Few-Shot 2: Endpoint autenticado

## Input
"Criar endpoint POST /api/flows/execute com JWT, validação de input e logs."

## Output (resumo)
- Endpoint FastAPI com `Depends(get_current_user)`
- Schemas Pydantic de request/response
- Tratamento de erro para 400/401/500
- Testes mínimos:
  1. sucesso com auth
  2. falha sem auth
  3. input inválido
  4. erro de serviço externo
