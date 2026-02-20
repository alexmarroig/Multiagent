# [NOME DO ENDPOINT]

## 1. CONTEXTO
Projeto: AgentOS Backend
Stack: FastAPI + Pydantic + Supabase
Módulo: [Auth / Agents / Flows / Tools]

## 2. INSTRUÇÕES

### 2.1 Requisitos Funcionais
- [ ] Endpoint retorna status 200 em sucesso
- [ ] Valida inputs com Pydantic
- [ ] Requer autenticação via JWT
- [ ] Retorna 401 se não autenticado
- [ ] Retorna 400 para input inválido
- [ ] Loga requisições relevantes

### 2.2 Estrutura Esperada
```text
api/
├── routes_[modulo].py
├── schemas.py
└── tests/
    └── test_[modulo].py
```

## 3. TAREFA
Implementar endpoint `[MÉTODO] /api/[caminho]`.

Deve:
- Usar `Depends(get_current_user)` para auth
- Validar inputs com Pydantic
- Retornar JSON estruturado
- Cobrir 5+ testes (happy path + erros)

## 4. SAÍDA ESPERADA
```python
@router.[metodo]("/[caminho]")
async def [funcao_nome](
    request: [RequestModel],
    user: dict = Depends(get_current_user),
) -> [ResponseModel]:
    ...
```
