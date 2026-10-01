# Paytriq — Campus Sponsorship Dealmaker

> Autonomous 6-agent mesh that finds sponsors, scores fit, negotiates, drafts MoUs, and sends outreach — with human approval gates.

## 6-Agent Mesh

| ID | Agent | Role |
|----|-------|------|
| A1 | Discovery & Intelligence | Ingests event, queries Maps, ranked prospect list |
| A2 | Match | Scores sponsor ↔ event fit (budget, audience, category) |
| A3 | Outreach & Negotiation | Gmail sequences, intent classification, meeting scheduling |
| A4 | Contract & Onboarding | Drafts localized MoU PDF from final terms |
| A5 | Pre-Event Compliance | Scans URLs/handles, vision-scrape, WhatsApp/Email nudge |
| A6 | Post-Event ROI Audit | Gemini Vision footfall/banner count + ROI report + learning update to A1 |

**Orchestration:** Supervisor-worker + blackboard (`EventState`). Supervisor routes tasks, enforces conditional edges and HITL interrupts. No agent talks peer-to-peer — all reads/writes go through `EventState`.

**Loops:**
- Loop A (Discovery): A1 → A2 → A1 — rescout if fit-pool < threshold
- Loop B (Negotiation): A3 → HITL → A3 — counter-offer iterations
- Loop C (Grounding): A4 → A5 → A4 — redraft until verification passes

See `docs/Design_Document.md` for full architecture + mermaid diagram.

## Quickstart

```bash
cd Paytriq-trial
pip install -r requirements.txt
pytest
uvicorn backend.main:app --reload
# in a new terminal / browser:
open frontend/index.html
# Windows: start frontend/index.html
```

Requirements: Python 3.10+, `GEMINI_API_KEY`, `GMAIL_USER` + `GMAIL_APP_PASSWORD` (or dry-run mode), `MAPS_API_KEY` (optional — JSON fallback included).

## Live Demo — 5-Min Script

| Time | Step | Command / Action |
|------|------|------------------|
| 0:00–0:45 | Intro + problem | "Clubs lose weeks cold-mailing shops. Paytriq closes sponsors in minutes." Show `frontend/index.html`. |
| 0:45–1:45 | Create event | Fill event form (name, footfall, budget, category) → POST `/api/events`. Show `EventState` JSON. |
| 1:45–2:45 | Scout + Match (Loop A) | Click "Find Sponsors" → POST `/api/sponsors/scout` → POST `/api/match`. Show ranked sponsor cards with fit scores. |
| 2:45–3:30 | Negotiate (Loop B) | Select sponsor → POST `/api/negotiate`. Show offer, simulate counter, show revised offer. Highlight HITL approve gate. |
| 3:30–4:15 | MoU (Loop C) | Click "Draft MoU" → POST `/api/mou/draft`. Show MoU preview, Verifier checklist pass. Click Approve → POST `/api/approvals`. |
| 4:15–5:00 | Send + close | Click "Send" → POST `/api/outreach/send` (dry-run if no creds). Show Gmail log + audit trail. Q&A. |

Fallback if offline: run `pytest` to show Loop A/B/C unit tests passing + open cached `frontend/index.html` demo data.

## Architecture Summary

```
frontend (React/index.html) → FastAPI (backend/main.py) → Supervisor → A1..A6 → EventState (blackboard)
Tools: Google Maps, Gmail API, Playwright, Gemini Vision
Memory: EventState (short-term blackboard) + JSON/Supabase deal history (long-term)
HITL gates: approve before send / counter / MoU sign-off
```

Custom lightweight graph runtime mirrors LangGraph semantics (nodes, conditional edges, interrupts) with zero infra cost — no LangSmith / LangGraph Server needed.

## API List

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/events` | Create event → initializes `EventState` |
| GET | `/api/events/{id}` | Get event + state snapshot |
| POST | `/api/sponsors/scout` | A1 Scout — discover sponsors (Maps/Playwright) |
| POST | `/api/match` | A2 Match — score + rank sponsors |
| POST | `/api/negotiate` | A3 Negotiator — generate offer / evaluate counter |
| POST | `/api/mou/draft` | A4 MoU Drafter — draft MoU from deal terms |
| POST | `/api/verify` | A5 Verifier — compliance check |
| POST | `/api/outreach/send` | A6 Outreach — send approved email (HITL-gated) |
| POST | `/api/approvals` | Approve / reject pending action (send, counter, MoU) |
| GET | `/api/audit/{event_id}` | Full audit trail from `EventState` |

All mutating send/counter/MoU routes return `status: pending_approval` until `/api/approvals` confirms.

## Team

- Aarohi Kondpalle — 23070122004
- Aditi Padole — 23070122014
- Archisha Yadav — 23070122041
- Aryan Srivastava — 23070122055
- CS-A, SIT

## Links

- Design Document: `docs/Design_Document.md`
- Synopsis: `docs/Synopsis.md`
- Frontend: `frontend/index.html`
- Backend entry: `backend/main.py`
- Tests: `pytest`
