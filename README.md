# Paytriq — Campus Sponsorship Dealmaker

> 6-agent mesh that finds sponsors, scores fit, negotiates, drafts MoUs, checks compliance, and audits ROI — with human approval gates.

## 6-Agent Mesh

| ID | Agent | Role |
|----|-------|------|
| A1 | Discovery & Intelligence | Ingests event, queries Maps, ranked prospect list |
| A2 | Pricing & Proposal | Bespoke decks + tiers, micro-tier revision on pushback |
| A3 | Outreach & Negotiation | Gmail sequences, intent classification, meeting scheduling |
| A4 | Contract & Onboarding | Drafts localized MoU PDF from final terms |
| A5 | Pre-Event Compliance | Scans URLs/handles, vision-scrape, WhatsApp/Email nudge |
| A6 | Post-Event ROI Audit | Gemini Vision footfall/banner count + ROI report + learning update to A1 |

**Orchestration:** Supervisor-worker + blackboard (`EventState`). Supervisor routes tasks, enforces conditional edges and HITL interrupts.

**Coordination loops:**
- Loop A (Negotiation): A3 classifies pushback -> A2 micro-tier -> A3 reply
- A3 Yes -> A4 MoU from A2 final terms -> A3 send for signature
- Loop B (Nudge): A5 scans promised logo, pings organizer if missing
- Loop C (Learning): A6 updates DB, A1 ranking weights for next event

See `docs/Design_Document.md` for full architecture + mermaid diagram.

## Prerequisites

- Python 3.10+
- No API keys needed (runs offline with mocks). Optional: `GEMINI_API_KEY`, `GOOGLE_MAPS_KEY` for live LLM/Maps.

## Steps to Run

### 1. Clone and install
```bash
git clone https://github.com/adroitathena2/Paytriq-trial
cd Paytriq-trial
pip install -r requirements.txt
```

### 2. Run tests (15 tests)
```bash
pytest -q
# expected: 15 passed
```

### 3. Run offline full demo (no server)
```bash
python scripts/run_demo.py
# prints: 11 brands, 5 proposals, 5 threads, MoU, compliance_score, ROI
```

### 4. Regenerate execution trace (for CA3 Section A evidence)
```bash
python scripts/generate_trace.py
# writes artifacts/trace_run1.jsonl (14 steps, Loops A/B/C)
```

### 5. Run API server
```bash
uvicorn backend.main:app --reload --port 8000
# health: http://localhost:8000/health
# docs: http://localhost:8000/docs
```

### 6. Use the UI
Open `http://localhost:8000/app` in a browser (served by the backend — do NOT
double-click `frontend/index.html` via `file://`, buttons will fail to reach the API).
- Prefill is TechFest Pune, 5000 footfall.
- Step 1 Create Event -> Step 2 Discovery -> Step 3 Proposal -> Step 4 approve + Send + Simulate pushback/yes -> Step 5 MoU + Compliance -> Step 6 ROI.
- API base auto-uses the page origin when served from `/app`. Green banner = connected.

### 7. Key API calls (curl)
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/event -H "Content-Type: application/json" -d @artifacts/input_sample.json
# copy event_id from response, then:
curl -X POST http://localhost:8000/api/propose -H "Content-Type: application/json" -d "{\"event_id\":\"<id>\"}"
curl -X POST http://localhost:8000/api/outreach/send -H "Content-Type: application/json" -d "{\"event_id\":\"<id>\",\"approve\":true}"
# simulate sponsor reply (pushback -> A2 revise, yes -> A4 MoU):
curl -X POST http://localhost:8000/api/gmail/webhook -H "Content-Type: application/json" -d "{\"event_id\":\"<id>\",\"from_brand\":\"Cafe Brewo\",\"body\":\"love it but only half budget\"}"
curl -X POST http://localhost:8000/api/contract/mou -H "Content-Type: application/json" -d "{\"event_id\":\"<id>\",\"brand\":\"Cafe Brewo\"}"
curl -X POST http://localhost:8000/api/compliance/check -H "Content-Type: application/json" -d "{\"event_id\":\"<id>\"}"
curl -X POST http://localhost:8000/api/audit/roi -H "Content-Type: application/json" -d "{\"event_id\":\"<id>\"}"
```

## Live Demo — 5-Min Script

| Time | Step | Action |
|------|------|--------|
| 0:00-0:45 | Intro | Show UI + problem: manual mails 4.8% reply |
| 0:45-1:45 | Create + Discover | Create event, show 11 ranked leads with fit-scores |
| 1:45-2:45 | Propose | Show brand-specific PDF tiers |
| 2:45-3:30 | Negotiate (Loop A) | Simulate pushback, show micro-tier revise, then Yes -> MoU |
| 3:30-4:15 | Comply (Loop B) | Show missing-logo nudge |
| 4:15-5:00 | Audit (Loop C) | Show ROI report + A1 weight update. Q&A |

Fallback offline: `pytest` + `python scripts/run_demo.py` + cached `artifacts/trace_run1.jsonl`.

## API List (actual)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | ok + event count |
| POST | `/api/event` | Create event + A1 discovery |
| POST | `/api/propose` | A2 proposals |
| POST | `/api/outreach/send` | A3 send, requires `approve:true` else gated |
| POST | `/api/gmail/webhook` | Incoming reply -> A2 revise or A4 MoU |
| POST | `/api/contract/mou` | A4 MoU PDF |
| POST | `/api/compliance/check` | A5 check + nudge |
| POST | `/api/audit/roi` | A6 ROI + learning |
| GET | `/api/state?event_id=` | EventState snapshot |

## Architecture Summary

```
frontend/index.html -> FastAPI backend/main.py -> Supervisor (graph.py) -> A1..A6 -> EventState
Tools: Maps, Gmail API, Playwright hook, Gemini Vision (all with offline fallback)
Memory: EventState (short-term) + JSON learning store (long-term)
HITL: approve before send / counter / MoU
```

Custom lightweight graph runtime mirrors LangGraph semantics (nodes, conditional edges, interrupts) with zero infra cost.

## Team

- Aarohi Kondpalle — 23070122004
- Aditi Padole — 23070122014
- Archisha Yadav — 23070122041
- Aryan Srivastava — 23070122055
- CS-A, SIT

## Links

- Design Document: `docs/Design_Document.md`
- Synopsis: `docs/Synopsis.md`
- Input sample: `artifacts/input_sample.json`
- Trace: `artifacts/trace_run1.jsonl`
