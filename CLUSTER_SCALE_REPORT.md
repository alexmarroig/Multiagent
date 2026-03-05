# Cluster Scale Report

| Agents | Queue Lag (ms) | Worker Utilization | Latency p95 (ms) | Token Usage | Cost Drift % |
|---:|---:|---:|---:|---:|---:|
| 100 | 54.58 | 46.54% | 70.67 | 11436 | 0.177 |
| 1000 | 90.77 | 60.38% | 102.79 | 90658 | 0.598 |
| 5000 | 183.59 | 96.00% | 157.19 | 524629 | 0.033 |

## Notes
- Workloads simulate mixed task complexity and periodic surge traffic.
- Cost drift remains bounded under 2%, satisfying billing integrity controls.
