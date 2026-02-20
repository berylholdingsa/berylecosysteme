"""Minimal secure PDF generator for certified statements."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from src.observability.logging.logger import logger


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(lines: list[str]) -> bytes:
    text_ops = ["BT", "/F1 10 Tf", "50 790 Td"]
    for idx, line in enumerate(lines):
        escaped = _escape_pdf_text(line)
        if idx > 0:
            text_ops.append("0 -14 Td")
        text_ops.append(f"({escaped}) Tj")
    text_ops.append("ET")
    content_stream = "\n".join(text_ops).encode("utf-8")

    objects: list[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(
        b"5 0 obj << /Length "
        + str(len(content_stream)).encode("ascii")
        + b" >> stream\n"
        + content_stream
        + b"\nendstream endobj\n"
    )

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_position = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(offsets)} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_position}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def generate_statement_pdf(
    *,
    merchant_name: str,
    user_id: str,
    period_label: str,
    period_start: str,
    period_end: str,
    total_sales: Decimal,
    total_charges: Decimal,
    net_result: Decimal,
    cashflow: Decimal,
    statement_fee: Decimal,
    currency: str,
    document_hash: str,
    verification_url: str,
) -> bytes:
    generated_at = datetime.now(timezone.utc).isoformat()
    qr_payload = f"verify:{verification_url}"

    lines = [
        "BERYL CERTIFIED MERCHANT STATEMENT",
        f"Merchant: {merchant_name}",
        f"Merchant ID: {user_id}",
        f"Period: {period_label} ({period_start} -> {period_end})",
        f"Total sales: {total_sales} {currency}",
        f"Total charges: {total_charges} {currency}",
        f"Net result: {net_result} {currency}",
        f"Cashflow: {cashflow} {currency}",
        f"Certified statement fee (1%): {statement_fee} {currency}",
        f"Document hash: {document_hash}",
        f"Verification endpoint: {verification_url}",
        f"QR verification payload: {qr_payload}",
        f"Generated at: {generated_at}",
        "This statement is immutable once signed.",
    ]

    pdf_bytes = _build_pdf(lines)
    logger.info(
        "event=bfos_statement_pdf_generated",
        merchant_id=user_id,
        period=period_label,
        hash=document_hash,
    )
    return pdf_bytes
