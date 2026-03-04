from monitoring.slo_monitor import SLOMonitor, SLOSnapshot, SLOThresholds


def test_slo_monitor_triggers_alert_incident_and_mitigation_for_each_violation():
    emitted_alerts = []
    recorded_incidents = []
    triggered_mitigations = []

    monitor = SLOMonitor(
        thresholds=SLOThresholds(
            task_success_rate_min=0.99,
            task_latency_max_seconds=2.0,
            queue_delay_max_seconds=1.0,
            worker_uptime_min=0.995,
        ),
        alert_emitter=emitted_alerts.append,
        incident_recorder=recorded_incidents.append,
        mitigation_workflow=triggered_mitigations.append,
    )

    incidents = monitor.evaluate(
        SLOSnapshot(
            task_success_rate=0.80,
            task_latency_seconds=3.7,
            queue_delay_seconds=4.2,
            worker_uptime=0.90,
        )
    )

    assert len(incidents) == 4
    assert {incident.metric for incident in incidents} == {
        "task_success_rate",
        "task_latency_seconds",
        "queue_delay_seconds",
        "worker_uptime",
    }

    assert len(emitted_alerts) == 4
    assert len(recorded_incidents) == 4
    assert len(triggered_mitigations) == 4
    assert all(incident.mitigation_triggered for incident in incidents)


def test_slo_monitor_does_not_emit_when_all_slos_are_healthy():
    monitor = SLOMonitor()

    incidents = monitor.evaluate(
        SLOSnapshot(
            task_success_rate=0.999,
            task_latency_seconds=1.5,
            queue_delay_seconds=0.2,
            worker_uptime=0.999,
        )
    )

    assert incidents == []
    assert monitor.alerts() == []
    assert monitor.incidents() == []
