"""HTTP response hardening headers (helmet-equivalent policy set)."""

from __future__ import annotations

from fastapi import Response

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "X-XSS-Protection": "0",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none';",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
}


def apply_security_headers(response: Response) -> None:
    for key, value in SECURITY_HEADERS.items():
        response.headers[key] = value
