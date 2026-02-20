"""
Auth Middleware for Zero-Trust enforcement.
"""

import logging
import uuid
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.v1.errors import resolve_correlation_id, unified_error_response
from src.core.security.jwt_rotation import TokenValidationError, jwt_rotation_service
from src.db.pg import get_conn
from src.observability.metrics.prometheus import Counter, Gauge

logger = logging.getLogger(__name__)

# Métriques Prometheus
auth_attempts_total = Counter('beryl_auth_attempts_total', 'Total authentication attempts', ['result', 'domain'])
auth_rejections_total = Counter('beryl_auth_rejections_total', 'Total authentication rejections', ['reason', 'domain'])
active_sessions = Gauge('beryl_active_sessions', 'Number of active authenticated sessions')


def _upsert_user(firebase_uid: str, email: Optional[str], phone: Optional[str]) -> str:
    """
    Crée ou met à jour un utilisateur dans la table 'users'
    via firebase_uid. Retourne l'id interne PostgreSQL.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (firebase_uid, email, phone)
                VALUES (%s, %s, %s)
                ON CONFLICT (firebase_uid) DO UPDATE
                SET email = COALESCE(EXCLUDED.email, users.email),
                    phone = COALESCE(EXCLUDED.phone, users.phone),
                    updated_at = now()
                RETURNING id
                """,
                (firebase_uid, email, phone),
            )
            user_id = cur.fetchone()[0]
            # Log définitif de l’opération d’upsert utilisateur
            print(f"[AUTH-UPSERT] firebase_uid={firebase_uid}, email={email}, phone={phone}, user_id={user_id}")
            conn.commit()
            return str(user_id)
    finally:
        conn.close()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = resolve_correlation_id(request)
        trace_id = request.headers.get("x-trace-id") or correlation_id or str(uuid.uuid4())
        request.state.trace_id = trace_id
        request.state.correlation_id = correlation_id

        # Skip auth for operational/public endpoints
        if request.url.path in [
            "/",
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/token-exchange",
            "/api/v2/esg/health",
            "/api/v2/esg/public-key",
            "/.well-known/greenos-public-key",
        ]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("401 Unauthorized: Missing or invalid token", extra={
                "trace_id": trace_id,
                "user_id": None,
                "scope": None,
                "domain": "unknown",
                "path": request.url.path,
                "method": request.method
            })
            auth_rejections_total.labels(reason='missing_token', domain='unknown').inc()
            return unified_error_response(
                request=request,
                status_code=401,
                code="AUTH_MISSING_TOKEN",
                message="Unauthorized",
            )

        token = auth_header.split(" ")[1]
        auth_attempts_total.labels(result='attempt', domain='unknown').inc()
        try:
            payload_data = jwt_rotation_service.verify(token)
            scopes = payload_data.get("scopes", [])
            domain = payload_data.get("domain", "unknown")
            user_id = payload_data.get("sub")
            firebase_uid = payload_data.get("firebase_uid") or payload_data.get("uid") or payload_data.get("sub")
            email = payload_data.get("email")
            phone = payload_data.get("phone_number") or payload_data.get("phone")

            if not firebase_uid:
                logger.warning("401 Unauthorized: Missing firebase subject", extra={
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "scope": scopes,
                    "domain": domain,
                    "path": request.url.path,
                    "method": request.method
                })
                auth_rejections_total.labels(reason='invalid_token', domain=domain).inc()
                return unified_error_response(
                    request=request,
                    status_code=401,
                    code="AUTH_INVALID_TOKEN",
                    message="Invalid token",
                )

            # Vérifier scope par domaine
            path = request.url.path
            required_scope = None
            if "/fintech" in path:
                required_scope = "fintech"
            elif "/mobility" in path:
                required_scope = "mobility"
            elif "/esg" in path:
                required_scope = "esg"
            elif "/social" in path:
                required_scope = "social"

            if required_scope and required_scope not in scopes:
                logger.warning(f"403 Forbidden: Invalid scope for {required_scope}", extra={
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "scope": scopes,
                    "domain": domain,
                    "path": request.url.path,
                    "method": request.method,
                    "required_scope": required_scope
                })
                auth_rejections_total.labels(reason='invalid_scope', domain=domain).inc()
                return unified_error_response(
                    request=request,
                    status_code=403,
                    code="AUTH_INVALID_SCOPE",
                    message="Forbidden",
                    details={"required_scope": required_scope},
                )

            # Synchronisation Firebase -> PostgreSQL
            try:
                pg_user_id = _upsert_user(str(firebase_uid), email, phone)
            except Exception:
                logger.exception("500 Internal Server Error: User persistence failed", extra={
                    "trace_id": trace_id,
                    "firebase_uid": firebase_uid,
                    "path": request.url.path,
                    "method": request.method
                })
                return unified_error_response(
                    request=request,
                    status_code=500,
                    code="AUTH_USER_PERSISTENCE_FAILED",
                    message="User persistence failed",
                )

            request.state.user = payload_data
            request.state.user_id = pg_user_id
            request.state.firebase_uid = str(firebase_uid)
            request.state.domain = domain
            request.state.scopes = scopes
            auth_attempts_total.labels(result='success', domain=domain).inc()

        except TokenValidationError as e:
            logger.warning(f"401 Unauthorized: Invalid token - {str(e)}", extra={
                "trace_id": trace_id,
                "user_id": None,
                "scope": None,
                "domain": "unknown",
                "path": request.url.path,
                "method": request.method,
                "error": str(e)
            })
            auth_rejections_total.labels(reason='invalid_token', domain='unknown').inc()
            message = str(e)
            code = "AUTH_INVALID_TOKEN"
            if "expired" in message.lower():
                code = "AUTH_TOKEN_EXPIRED"
            return unified_error_response(
                request=request,
                status_code=401,
                code=code,
                message=message or "Invalid token",
            )

        response = await call_next(request)
        return response
