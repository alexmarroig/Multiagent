from agentos.monitoring.alerts import AlertManager
from agentos.monitoring.anomaly_detector import RollingAnomalyDetector


def test_rolling_anomaly_detector_flags_all_runtime_metrics():
    detector = RollingAnomalyDetector(window_size=12, min_samples=5, z_score_threshold=1.5)

    baseline_points = [
        {"error_rate": 0.01, "queue_depth": 10, "task_latency": 0.95, "worker_crashed": False},
        {"error_rate": 0.02, "queue_depth": 11, "task_latency": 1.05, "worker_crashed": False},
        {"error_rate": 0.01, "queue_depth": 9, "task_latency": 1.0, "worker_crashed": False},
        {"error_rate": 0.015, "queue_depth": 10, "task_latency": 1.1, "worker_crashed": False},
        {"error_rate": 0.01, "queue_depth": 10, "task_latency": 0.98, "worker_crashed": True},
    ]

    for point in baseline_points:
        assert detector.detect_runtime_anomalies(**point) == []

    anomalies = detector.detect_runtime_anomalies(
        error_rate=0.2,
        queue_depth=50,
        task_latency=4.0,
        worker_crashed=True,
    )

    metrics = {anomaly.metric for anomaly in anomalies}
    assert metrics == {"error_rate", "queue_depth", "task_latency", "agent_crash_frequency"}


def test_alert_manager_emits_anomaly_alerts_for_runtime_spikes():
    manager = AlertManager(
        queue_high_watermark=10_000,
        error_rate_threshold=1.0,
        repeated_worker_crashes=10,
        anomaly_window_size=12,
        anomaly_min_samples=5,
        anomaly_z_score_threshold=1.5,
    )

    baseline_points = [
        {"error_rate": 0.01, "queue_depth": 10, "task_latency": 0.95, "worker_crashed": False},
        {"error_rate": 0.02, "queue_depth": 11, "task_latency": 1.05, "worker_crashed": False},
        {"error_rate": 0.01, "queue_depth": 9, "task_latency": 1.0, "worker_crashed": False},
        {"error_rate": 0.015, "queue_depth": 10, "task_latency": 1.1, "worker_crashed": False},
        {"error_rate": 0.01, "queue_depth": 10, "task_latency": 0.98, "worker_crashed": True},
    ]

    for point in baseline_points:
        alerts = manager.evaluate_runtime_signals(worker_id="worker-1", llm_cost=0.0, **point)
        assert alerts == []

    alerts = manager.evaluate_runtime_signals(
        worker_id="worker-1",
        error_rate=0.2,
        queue_depth=50,
        task_latency=4.0,
        worker_crashed=True,
        llm_cost=0.0,
    )

    categories = {alert.category for alert in alerts}
    assert categories == {
        "error_rate_anomaly",
        "queue_depth_anomaly",
        "task_latency_anomaly",
        "agent_crash_frequency_anomaly",
    }
