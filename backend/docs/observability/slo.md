# SLOs mínimos e política de erro orçado

## SLOs

1. **Latência p95 de execução (`runs.total_time_p95_seconds`)**
   - Objetivo: **<= 45s** por janela móvel de 30 dias.
2. **Disponibilidade da API (`/health` e endpoints críticos)**
   - Objetivo: **>= 99.5%** mensal.
3. **Taxa de erro por integração externa (`external_integrations.*.error_rate`)**
   - Objetivo: **< 5%** por tool em janela de 7 dias.
4. **Falhas de websocket (`websocket.failures`)**
   - Objetivo: **< 1%** das sessões ativas por dia.

## Política de erro orçado

- Com SLO de 99.5% de disponibilidade, orçamento mensal é ~**3h39m** de indisponibilidade.
- Com SLO de erro externo em 5%, orçamento mensal é **5 falhas a cada 100 chamadas** por integração.

### Ações por consumo do orçamento

- **<= 50%** consumido: operação normal + melhorias planejadas.
- **50% a 80%** consumido: congelar features não-críticas e priorizar hardening.
- **> 80%** consumido: foco total em confiabilidade (rollback de mudanças arriscadas, plantão reforçado).
- **100%** consumido: gate de releases até retorno à estabilidade.

## Indicadores usados no dashboard

- `tasks.<task_id>.p95_seconds`
- `tools.<tool_id>.error_rate`
- `runs.total_time_p95_seconds`
- `runs.backlog_running`
- `websocket.failures`
