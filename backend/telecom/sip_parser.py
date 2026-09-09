import re
from typing import List

from .models import SIPEvent

_STATUS_RE = re.compile(r"\b(SIP/2\.0)\s+(\d{3})\s*(.*)", re.IGNORECASE)
_METHOD_RE = re.compile(r"^(REGISTER|INVITE|ACK|BYE|CANCEL|OPTIONS|PRACK|UPDATE|SUBSCRIBE|NOTIFY|REFER|INFO|MESSAGE)\b", re.IGNORECASE)
_CALL_ID_RE = re.compile(r"^Call-ID:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_FROM_RE = re.compile(r"^From:.*?(?:sip:)?([^@;>\s]+)", re.IGNORECASE | re.MULTILINE)
_TO_RE = re.compile(r"^To:.*?(?:sip:)?([^@;>\s]+)", re.IGNORECASE | re.MULTILINE)


def parse_sip_log(text: str) -> List[SIPEvent]:
    """Parse common SIP start-lines from a log into normalized events.

    This is intentionally deterministic; LLMs are not used to interpret protocol fields.
    """
    events: List[SIPEvent] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        status_match = _STATUS_RE.search(line)
        method_match = _METHOD_RE.search(line)
        if not status_match and not method_match:
            continue
        status_code = int(status_match.group(2)) if status_match else None
        reason = status_match.group(3).strip() if status_match else None
        method = method_match.group(1).upper() if method_match else None
        events.append(SIPEvent(method=method, status_code=status_code, reason=reason, raw=line))
    return events


def analyze_sip_text(text: str) -> dict:
    events = parse_sip_log(text)
    findings: List[str] = []
    causes: List[str] = []
    checks: List[str] = []
    severity = "info"

    codes = [e.status_code for e in events if e.status_code is not None]
    if 403 in codes:
        findings.append("SIP 403 Forbidden detected: the request was rejected by policy or authentication/authorization rules.")
        causes.extend(["Invalid credentials or authentication configuration", "User/device not authorized", "SIP policy or ACL rejection"])
        checks.extend(["Verify SIP username/password and authentication realm", "Check account state and SIP ACL/policy", "Correlate the 403 with the preceding REGISTER/INVITE exchange"])
        severity = "high"
    elif 401 in codes:
        findings.append("SIP 401 Unauthorized detected: an authentication challenge was returned.")
        checks.extend(["Inspect the subsequent authenticated request", "Verify authentication credentials and realm"])
        severity = "medium"
    elif 503 in codes:
        findings.append("SIP 503 Service Unavailable detected: the target service or upstream path may be unavailable.")
        causes.extend(["SIP service/SBC unavailable", "Upstream dependency unavailable", "Capacity or overload condition"])
        checks.extend(["Check PBX/SBC service health", "Check upstream routing and connectivity", "Check concurrent calls and resource utilization"])
        severity = "high"
    elif any(code is not None and 500 <= code <= 599 for code in codes):
        findings.append("A SIP 5xx server-side failure was detected.")
        severity = "high"
    elif any(code is not None and 400 <= code <= 499 for code in codes):
        findings.append("A SIP 4xx client/request-side failure was detected.")
        severity = "medium"

    if not events:
        findings.append("No recognizable SIP start-lines were found in the supplied text.")

    status = "failed" if any(code is not None and code >= 400 for code in codes) else "observed"
    return {
        "protocol": "SIP",
        "status": status,
        "events": [e.model_dump() for e in events],
        "findings": findings,
        "probable_causes": causes,
        "severity": severity,
        "evidence": [e.raw for e in events],
        "recommended_checks": checks,
    }
