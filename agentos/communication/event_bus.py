"""Backwards-compatible event bus module now backed by the durable event stream."""

from agentos.communication.durable_event_bus import DurableEventBus, Event

EventBus = DurableEventBus

__all__ = ["Event", "EventBus", "DurableEventBus"]
