# [INTEGRAÇÃO EXTERNA]

## 1. CONTEXTO
API externa: [nome]
Arquivo: `backend/tools/[nome]_client.py`

## 2. INSTRUÇÕES
- [ ] API key via env
- [ ] Retry 3x
- [ ] Timeout 30s
- [ ] Fallback em indisponibilidade
- [ ] Mock para testes

## 3. TAREFA
Implementar client HTTP e tool de uso.

## 4. SAÍDA ESPERADA
- Client isolado
- Testes cobrindo timeout, 401, 500 e network error
