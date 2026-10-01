"""A4 Contract: draft MoU dict + PDF from exact proposal terms."""
from __future__ import annotations

from typing import Dict

from ..state import EventProfile, Proposal
from ..tools.pdf import make_mou_pdf


def draft_mou(event: EventProfile, final_proposal: Proposal, out_dir: str = "out") -> Dict[str, object]:
    """Build MoU payload and PDF; returns dict with pdf_path."""
    terms = f"{final_proposal.tier} @ Rs.{final_proposal.amount}; deliverables: " + \
        ", ".join(final_proposal.deliverables)
    data = {"event": event.name, "brand": final_proposal.brand,
            "amount": final_proposal.amount, "terms": terms}
    pdf_path = f"{out_dir}/mou_{final_proposal.brand.replace(' ', '_')}.pdf"
    pdf_path = make_mou_pdf(data, pdf_path)
    return {**data, "pdf_path": pdf_path}
