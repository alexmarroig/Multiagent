from tests.cluster.benchmark_harness import run_default_benchmark


def test_cluster_benchmark_profiles() -> None:
    results = run_default_benchmark()
    assert [r.agents for r in results] == [100, 1000, 5000]
    assert all(r.worker_utilization > 0 for r in results)
    assert all(r.cost_drift_pct < 5.0 for r in results)
