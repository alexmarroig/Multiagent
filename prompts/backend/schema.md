# [NOME DOS SCHEMAS]

## 1. CONTEXTO
Projeto: AgentOS Backend
Módulo: `backend/api/schemas.py`

## 2. INSTRUÇÕES
- [ ] Definir RequestModel/ResponseModel
- [ ] Constraints com `Field(...)`
- [ ] Tipagem clara para payloads
- [ ] Compatível com endpoint e testes

## 3. TAREFA
Criar schemas para [feature].

## 4. SAÍDA ESPERADA
```python
class [RequestModel](BaseModel):
    field1: str
    field2: int = Field(gt=0)

class [ResponseModel](BaseModel):
    status: str
    data: dict
```
