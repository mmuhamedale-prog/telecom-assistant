# AI Telecom Assistant — Live Demo

Recruiter-facing AI telecom engineering copilot combining an LLM backend, telecom-specific reasoning, and real-time voice input.

## Implemented
- Free-form LLM chat — no hardcoded keyword/question limitation.
- Senior telecom engineering reasoning for SIP/VoIP, SBC/RTP/DNS, IP/MPLS, L2/L3, GSM-R/FRMCS, PAGA/PABX and railway OCC/CTC/PIS troubleshooting.
- Structured incident reasoning: assessment, analysis, ranked root causes, evidence, troubleshooting, corrective action, severity/impact and verification.
- Conversation history for contextual follow-up questions.
- Browser real-time STT: microphone → live transcript → transcript automatically sent to the LLM chat pipeline.
- Server-side `/transcribe` endpoint for uploaded audio.
- API key remains server-side and is never embedded in the frontend.

## Architecture
`Recruiter → GitHub Pages UI → FastAPI → OpenAI Responses API → Telecom Engineering Reasoning`

`Microphone → Browser STT → Transcript → FastAPI /chat → LLM`

`Audio file → FastAPI /transcribe → OpenAI transcription → text → /chat`

## Model selection
The backend defaults to `gpt-5.6-terra`, which OpenAI documents as its GPT-5.6 model balancing intelligence and cost. Speech transcription defaults to `gpt-4o-transcribe`. The model choices are configurable through environment variables.

## Deployment note
GitHub Pages is static hosting, so it cannot run the FastAPI/OpenAI backend itself. Deploy `backend/` on a Python host, set `OPENAI_API_KEY` there, then paste the backend URL into the frontend's **Backend API URL** field. GitHub Pages remains the recruiter-facing UI.

Never commit an API key; keep it server-side.

## Backend
```text
backend/
  main.py
  requirements.txt
  .env.example
```

## Original Project Package
The original implementation package remains included as `AI-Telecom-Assistant-Live-Demo.zip`.
