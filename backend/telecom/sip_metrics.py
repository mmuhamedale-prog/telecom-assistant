from datetime import datetime
from typing import Dict, List

from .models import SIPEvent


def calculate_sip_metrics(events: List[SIPEvent]) -> Dict[str, object]:
    """Calculate timing and volume metrics from events when timestamps exist."""
    timestamps = [event.timestamp for event in events if event.timestamp is not None]
    duration_seconds = None
    if len(timestamps) >= 2:
        ordered = sorted(timestamps)
        duration_seconds = (ordered[-1] - ordered[0]).total_seconds()

    return {
        "event_count": len(events),
        "call_ids": len({event.call_id for event in events if event.call_id}),
        "duration_seconds": duration_seconds,
        "status_code_counts": _status_counts(events),
        "timestamp_coverage": len(timestamps) / len(events) if events else 0.0,
    }


def _status_counts(events: List[SIPEvent]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for event in events:
        if event.status_code is not None:
            key = str(event.status_code)
            counts[key] = counts.get(key, 0) + 1
    return counts
