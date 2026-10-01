"""PDF generation with graceful fallback (no reportlab => .html + .txt)."""
from __future__ import annotations

import os
from typing import Dict


def _fallback(data: Dict[str, object], out_path: str, title: str) -> str:
    """Write .html + .txt alongside out_path; return out_path."""
    base, _ = os.path.splitext(out_path)
    lines = [f"# {title}"] + [f"- {k}: {v}" for k, v in data.items()]
    text = "\n".join(lines)
    html = "<html><body><h1>%s</h1><ul>%s</ul></body></html>" % (
        title, "".join(f"<li><b>{k}</b>: {v}</li>" for k, v in data.items()))
    try:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(base + ".html", "w", encoding="utf-8") as f:
            f.write(html)
        with open(base + ".txt", "w", encoding="utf-8") as f:
            f.write(text)
        with open(out_path, "w", encoding="utf-8") as f:  # placeholder so pdf_path exists
            f.write(text)
    except Exception:
        pass
    return out_path


def _try_reportlab(lines: list[str], out_path: str) -> bool:
    try:
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        c = canvas.Canvas(out_path, pagesize=A4)
        y = 800.0
        for line in lines:
            c.drawString(50, y, str(line)[:95])
            y -= 18
            if y < 50:
                c.showPage()
                y = 800.0
        c.save()
        return True
    except Exception:
        return False


def make_proposal_pdf(data: Dict[str, object], out_path: str) -> str:
    """Build sponsor proposal PDF (or fallback)."""
    lines = ["Paytriq Proposal", f"Brand: {data.get('brand')}",
             f"Tier: {data.get('tier')} @ Rs.{data.get('amount')}"] + \
            [f"- {d}" for d in data.get("deliverables", [])]  # type: ignore
    if not _try_reportlab(lines, out_path):
        return _fallback(data, out_path, "Paytriq Proposal")
    return out_path


def make_mou_pdf(data: Dict[str, object], out_path: str) -> str:
    """Build MoU PDF (or fallback)."""
    lines = ["Paytriq MoU", f"Event: {data.get('event')}", f"Brand: {data.get('brand')}",
             f"Amount: Rs.{data.get('amount')}", f"Terms: {data.get('terms')}"]
    if not _try_reportlab(lines, out_path):
        return _fallback(data, out_path, "Paytriq MoU")
    return out_path


def make_roi_pdf(data: Dict[str, object], out_path: str) -> str:
    """Build ROI report PDF (or fallback)."""
    lines = ["Paytriq ROI Report"] + [f"{k}: {v}" for k, v in data.items()]
    if not _try_reportlab(lines, out_path):
        return _fallback(data, out_path, "Paytriq ROI Report")
    return out_path
