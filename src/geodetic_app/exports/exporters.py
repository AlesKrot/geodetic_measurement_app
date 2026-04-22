from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_csv(frame: pd.DataFrame, destination: str | Path) -> Path:
    path = Path(destination)
    frame.to_csv(path, index=False)
    return path


def export_json(frame: pd.DataFrame, destination: str | Path) -> Path:
    path = Path(destination)
    frame.to_json(path, orient="records", indent=2, date_format="iso")
    return path


def export_pdf(frame: pd.DataFrame, destination: str | Path) -> Path:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("PDF export requires reportlab") from exc

    path = Path(destination)
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y_position = height - 40
    pdf.setFont("Helvetica", 12)
    pdf.drawString(40, y_position, "Geodetic Measurement Report")
    y_position -= 30
    pdf.setFont("Helvetica", 9)
    for line in frame.head(40).to_string(index=False).splitlines():
        pdf.drawString(40, y_position, line[:120])
        y_position -= 14
        if y_position < 50:
            pdf.showPage()
            y_position = height - 40
            pdf.setFont("Helvetica", 9)
    pdf.save()
    return path
