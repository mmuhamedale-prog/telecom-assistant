import re
from typing import Dict, List

_SDP_CONNECTION_RE = re.compile(r"^c=IN IP(?:4|6)\s+(\S+)", re.IGNORECASE | re.MULTILINE)
_SDP_MEDIA_RE = re.compile(r"^m=(audio|video)\s+(\d+)\s+([^\s]+)\s+(.+)$", re.IGNORECASE | re.MULTILINE)


def analyze_sdp(text: str) -> Dict[str, object]:
    """Extract the core SDP media parameters needed for SIP/RTP troubleshooting."""
    connection = _SDP_CONNECTION_RE.search(text)
    media: List[Dict[str, object]] = []
    for match in _SDP_MEDIA_RE.finditer(text):
        media.append({
            "media": match.group(1).lower(),
            "port": int(match.group(2)),
            "transport": match.group(3),
            "payload_types": [item for item in match.group(4).split() if item.isdigit()],
        })
    return {"connection_address": connection.group(1) if connection else None, "media": media}


def correlate_sip_rtp(sip_events: list, rtp_observed: bool) -> Dict[str, object]:
    """Provide a minimal SIP/RTP correlation result without inventing RTP telemetry."""
    invite_present = any(getattr(event, "method", None) == "INVITE" for event in sip_events)
    return {
        "sip_invite_observed": invite_present,
        "rtp_observed": rtp_observed,
        "media_path_status": "observed" if invite_present and rtp_observed else "not_confirmed",
    }
