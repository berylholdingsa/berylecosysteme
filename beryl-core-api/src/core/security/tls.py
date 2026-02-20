"""Transport security helpers."""

from __future__ import annotations

from fastapi import Request


def request_uses_tls(request: Request) -> bool:
    proto = request.headers.get("x-forwarded-proto", "").lower()
    if proto:
        return proto == "https"
    return request.url.scheme == "https"
