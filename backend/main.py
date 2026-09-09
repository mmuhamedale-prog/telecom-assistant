import os
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

from telecom.sip_parser import analyze_sip_text
from telecom.models import TelecomRealtimeEvent

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

app = FastAPI(title="AI Telecom Assistant API", version="2.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """You are an expert AI Telecom Engineering Assistant.

Answer free-form engineering questions; never restrict the user to predefined scenarios.
Reason like a senior telecom/network/railway communications engineer. Cover SIP/VoIP,
SBC/proxy, RTP, DNS, IP/MPLS, L2/L3, LAN/WAN, VPN, SDH/DWDM, GSM-R/FRMCS, private LTE/5G,
PAGA, PABX, CCTV, NMS, SCADA/OT, OCC/CTC/PIS and telecom incident troubleshooting when relevant.

For technical incidents, structure the answer as:
1. Assessment / problem interpretation
2. Technical analysis
3. Most likely root causes (ranked)
4. Evidence/telemetry to collect
5. Step-by-step troubleshooting
6. Recommended corrective action
7. Severity and service impact
8. Verification / rollback checks

Do not invent logs, measurements, topology, vendor behavior, or configuration values.
Clearly distinguish facts from hypotheses. Ask for missing evidence when it materially affects the diagnosis.
Be practical and precise. Prefer protocol-level details, commands or checks only when appropriate.
If the user provides a transcript from speech, treat it exactly like a normal engineering question.
"""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []


@app.get("/")
def root():
    return {"service": "AI Telecom Assistant API", "model": MODEL, "status": "online", "telecom_intelligence": "enabled"}


@app.get("/health")
def health():
    return {"status": "ok", "llm_configured": client is not None, "model": MODEL, "telecom_intelligence": "enabled"}


@app.post("/telecom/analyze/sip")
async def analyze_sip(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A SIP log file is required.")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="SIP log is too large.")
    text = data.decode("utf-8", errors="replace")
    return analyze_sip_text(text)


@app.post("/chat")
def chat(request: ChatRequest):
    if client is None:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured on the backend.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in request.history[-12:]:
        if item.role in {"user", "assistant"} and item.content.strip():
            messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": request.message.strip()})

    try:
        response = client.responses.create(model=MODEL, input=messages, temperature=0.2)
        return {"answer": response.output_text, "model": MODEL}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {type(exc).__name__}")


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if client is None:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured on the backend.")
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Please upload an audio file.")
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file is too large.")
    try:
        result = client.audio.transcriptions.create(
            model=TRANSCRIBE_MODEL,
            file=(file.filename or "audio.webm", data, file.content_type),
            prompt="Telecom engineering vocabulary: SIP, INVITE, ACK, BYE, 4xx, 5xx, SBC, RTP, DNS, MPLS, VLAN, BGP, OSPF, GSM-R, FRMCS, PAGA, PABX, OCC, CTC, PIS.",
        )
        return {"text": result.text, "model": TRANSCRIBE_MODEL}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {type(exc).__name__}")


@app.websocket("/ws/telecom")
async def telecom_websocket(websocket: WebSocket):
    """Real-time telecom event ingress for Asterisk/UC adapters and live dashboards."""
    await websocket.accept()
    await websocket.send_json({"type": "connected", "service": "telecom-realtime"})
    try:
        while True:
            payload = await websocket.receive_json()
            event = TelecomRealtimeEvent.model_validate(payload)
            await websocket.send_json({"type": "telecom_event", "event": event.model_dump(mode="json")})
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await websocket.send_json({"type": "error", "detail": type(exc).__name__})
        await websocket.close(code=1003)
