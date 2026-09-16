from typing import Dict, List

from .models import SIPEvent


def analyze_sip_events(events: List[SIPEvent]) -> Dict[str, object]:
    """Detect common enterprise SIP signaling failures from normalized events."""
    codes = [e.status_code for e in events if e.status_code is not None]
    methods = [e.method for e in events if e.method]
    findings: List[str] = []
    causes: List[str] = []
    checks: List[str] = []
    severity = "info"

    if 401 in codes:
        findings.append("401 Unauthorized authentication challenge detected.")
        checks.append("Verify authentication exchange, credentials, and realm.")
        severity = "medium"
    if 403 in codes:
        findings.append("403 Forbidden rejection detected.")
        causes.extend(["Authentication/authorization policy", "SIP ACL or account restriction"])
        checks.extend(["Check SIP account state", "Check ACL/policy", "Correlate with the preceding request"])
        severity = "high"
    if 404 in codes:
        findings.append("404 Not Found detected: requested SIP destination may not exist or be routable.")
        checks.append("Verify dial plan, destination and SIP routing.")
        severity = max(severity, "medium", key={"info": 0, "medium": 1, "high": 2}.get)
    if 408 in codes:
        findings.append("408 Request Timeout detected.")
        causes.append("No timely response from the SIP peer or upstream path")
        checks.append("Check SIP reachability, routing, firewall/NAT and retransmissions.")
        severity = "high"
    if 480 in codes or 486 in codes:
        findings.append("SIP destination availability/busy response detected.")
        checks.append("Correlate the response with endpoint registration and call state.")
        severity = max(severity, "medium", key={"info": 0, "medium": 1, "high": 2}.get)
    if 503 in codes:
        findings.append("503 Service Unavailable detected.")
        causes.append("SIP service, SBC, upstream dependency or capacity issue")
        checks.extend(["Check PBX/SBC health", "Check upstream routing/connectivity", "Check resource utilization"])
        severity = "high"
    if any(500 <= code <= 599 for code in codes):
        findings.append("SIP 5xx server-side failure detected.")
        severity = "high"

    if "INVITE" in methods and "ACK" not in methods and 200 in codes:
        findings.append("200 OK to INVITE observed without a corresponding ACK in the supplied events.")
        checks.append("Verify complete INVITE transaction and possible ACK loss/routing issues.")
        severity = "high"

    return {
        "findings": findings,
        "probable_causes": causes,
        "severity": severity,
        "recommended_checks": checks,
    }
