# [PYDANTIC SCHEMAS]

## 1. CONTEXTO
Módulo: `backend/api/schemas.py`

## 2. INSTRUÇÕES
- [ ] Campos obrigatórios e opcionais claros
- [ ] Constraints (`Field(gt=0)`, regex etc.)
- [ ] Mensagens de erro úteis

## 3. TAREFA
Definir `RequestModel` e `ResponseModel` para [feature].

## 4. SAÍDA ESPERADA
```py
class [RequestModel](BaseModel):
    field1: str

class [ResponseModel](BaseModel):
    status: str
    data: dict
```
