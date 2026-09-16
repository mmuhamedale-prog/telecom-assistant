from typing import Dict, List

from .models import SIPEvent


def correlate_sip_flow(events: List[SIPEvent]) -> Dict[str, object]:
    """Build a lightweight call/dialog view from parsed SIP events."""
    calls: Dict[str, Dict[str, object]] = {}
    uncorrelated: List[SIPEvent] = []

    for event in events:
        if not event.call_id:
            uncorrelated.append(event)
            continue
        call = calls.setdefault(
            event.call_id,
            {"call_id": event.call_id, "events": [], "methods": [], "status_codes": []},
        )
        call["events"].append(event.model_dump())
        if event.method:
            call["methods"].append(event.method)
        if event.status_code is not None:
            call["status_codes"].append(event.status_code)

    for call in calls.values():
        methods = call["methods"]
        call["completed"] = "INVITE" in methods and (200 in call["status_codes"] or "BYE" in methods)
        call["has_failure"] = any(code >= 400 for code in call["status_codes"])

    return {"calls": list(calls.values()), "uncorrelated_events": [e.model_dump() for e in uncorrelated]}
