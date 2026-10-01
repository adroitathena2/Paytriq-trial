# Paytriq — Synopsis

College event teams lose weeks cold-mailing nearby shops with generic pitches, no fit data, and no follow-through — sponsors ignore them, negotiations stall over WhatsApp, and MoUs are copy-pasted without verification. The result is underfunded fests and hackathons despite strong local footfall that neighbourhood businesses would pay to reach.

Paytriq is a Campus Sponsorship Dealmaker built as a supervised 6-agent mesh over a shared EventState blackboard. Scout (A1) discovers sponsors via Maps, Playwright, and Vision; Match (A2) ranks fit; Negotiator (A3) iterates offers; MoU Drafter (A4) drafts agreements; Verifier (A5) enforces grounding and compliance; and Outreach (A6) sends Gmail messages — all routed by a Supervisor with three human approval gates (send, counter, MoU) and three bounded loops for discovery, negotiation, and redrafting.

Built for student sponsorship cells and event coordinators, Paytriq runs as a FastAPI backend with a simple web frontend, Gemini Pro for reasoning agents and Flash for fast agents, and Supabase with JSON fallback — turning weeks of manual outreach into an auditable five-minute demo from event creation to approved MoU and sent email.
