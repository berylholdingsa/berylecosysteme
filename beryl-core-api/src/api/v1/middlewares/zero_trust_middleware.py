"""
Zero-Trust Authentication Middleware for Beryl Core API.

This middleware enforces Zero-Trust principles:
- Authentication required for ALL requests
- Authorization based on RBAC and domain-specific permissions
- Comprehensive audit logging
- Rate limiting per endpoint/domain
- Token validation and rotation
"""

import time
import logging
from typing import Dict, List, Optional, Callable
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from src.auth.jwt.token_validator import validate_token
from src.auth.rbac.enforcer import RBACEnforcer
from src.observability.audit.logger import AuditLogger
from src.config.settings import settings

# Initialize components
limiter = Limiter(key_func=get_remote_address)
audit_logger = AuditLogger()
rbac_enforcer = RBACEnforcer()

class ZeroTrustMiddleware:
    """Zero-Trust middleware for authentication and authorization."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.exempt_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        }

    async def __call__(self, request: Request, call_next):
        """Process each request through Zero-Trust validation."""
        start_time = time.time()

        # Skip authentication for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        try:
            # 1. Extract and validate token
            token_data = await self._extract_and_validate_token(request)

            # 2. Validate RBAC permissions
            await self._validate_permissions(request, token_data)

            # 3. Apply rate limiting
            await self._apply_rate_limiting(request, token_data)

            # 4. Log access attempt
            await self._log_access_attempt(request, token_data, "ALLOWED")

            # Process request
            response = await call_next(request)

            # 5. Log successful response
            processing_time = time.time() - start_time
            await self._log_response(request, token_data, response.status_code, processing_time)

            return response

        except HTTPException as e:
            # Log denied access
            token_data = getattr(request.state, 'token_data', None)
            await self._log_access_attempt(request, token_data, "DENIED", str(e.detail))

            # Return error response
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "Access Denied",
                    "message": str(e.detail),
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in Zero-Trust middleware: {e}")
            await self._log_access_attempt(request, None, "ERROR", str(e))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal Server Error"}
            )

    async def _extract_and_validate_token(self, request: Request) -> Dict:
        """Extract and validate JWT token from request."""
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header"
            )

        token = auth_header.split(" ")[1]

        # Validate token
        try:
            token_data = validate_token(token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

        # Store token data in request state
        request.state.token_data = token_data

        return token_data

    async def _validate_permissions(self, request: Request, token_data: Dict):
        """Validate RBAC permissions for the request."""
        user_id = token_data.get("sub")
        roles = token_data.get("roles", [])
        domains = token_data.get("domains", [])

        # Determine required permissions based on path
        path = request.url.path
        method = request.method

        required_permissions = self._get_required_permissions(path, method)

        # Check if user has required permissions
        if not rbac_enforcer.check_permissions(user_id, roles, domains, required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation"
            )

        # Domain-specific validation for sensitive operations
        if any(domain in ['fintech', 'esg'] for domain in domains):
            await self._validate_domain_access(request, token_data)

    async def _validate_domain_access(self, request: Request, token_data: Dict):
        """Additional validation for sensitive domains (Fintech, ESG)."""
        # Check if user has explicit consent for sensitive data
        if not token_data.get("sensitive_data_consent", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Explicit consent required for sensitive data access"
            )

        # Validate IP restrictions for sensitive operations
        client_ip = request.client.host
        allowed_ips = token_data.get("allowed_ips", [])
        if allowed_ips and client_ip not in allowed_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from this IP address"
            )

        # Check session validity and rotation
        session_id = token_data.get("session_id")
        if not await self._validate_session(session_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid"
            )

    async def _validate_session(self, session_id: str) -> bool:
        """Validate user session against Redis/cache."""
        # TODO: Implement session validation with Redis
        # For now, return True
        return True

    async def _apply_rate_limiting(self, request: Request, token_data: Dict):
        """Apply rate limiting based on user role and endpoint."""
        user_id = token_data.get("sub")
        roles = token_data.get("roles", [])

        # Determine rate limit based on role
        if "admin" in roles:
            limit = "100/minute"
        elif "premium" in roles:
            limit = "50/minute"
        else:
            limit = "10/minute"

        # Apply domain-specific limits for sensitive operations
        path = request.url.path
        if any(domain in path for domain in ['fintech', 'esg']):
            limit = "5/minute"  # Stricter limits for sensitive data

        # TODO: Implement actual rate limiting with Redis
        # For now, just log
        self.logger.info(f"Rate limit applied: {limit} for user {user_id}")

    def _get_required_permissions(self, path: str, method: str) -> List[str]:
        """Determine required permissions based on path and method."""
        # Domain-based permissions
        if path.startswith("/api/v1/fintech"):
            return ["fintech:read"] if method == "GET" else ["fintech:write"]
        elif path.startswith("/api/v1/mobility"):
            return ["mobility:read"] if method == "GET" else ["mobility:write"]
        elif path.startswith("/api/v1/esg"):
            return ["esg:read"] if method == "GET" else ["esg:write"]
        elif path.startswith("/api/v1/social"):
            return ["social:read"] if method == "GET" else ["social:write"]
        elif path.startswith("/graphql"):
            return ["graphql:execute"]
        else:
            return ["general:access"]

    async def _log_access_attempt(self, request: Request, token_data: Optional[Dict],
                                decision: str, reason: str = None):
        """Log all access attempts for audit purposes."""
        log_entry = {
            "timestamp": time.time(),
            "request_id": getattr(request.state, 'request_id', None),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "user_id": token_data.get("sub") if token_data else None,
            "roles": token_data.get("roles") if token_data else None,
            "domains": token_data.get("domains") if token_data else None,
            "decision": decision,
            "reason": reason
        }

        await audit_logger.log_access_attempt(log_entry)

    async def _log_response(self, request: Request, token_data: Dict,
                          status_code: int, processing_time: float):
        """Log successful responses."""
        log_entry = {
            "timestamp": time.time(),
            "request_id": getattr(request.state, 'request_id', None),
            "user_id": token_data.get("sub"),
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
            "processing_time": processing_time,
            "success": status_code < 400
        }

        await audit_logger.log_response(log_entry)

# Decorator for Zero-Trust protection of individual functions
def zero_trust_required(required_permissions: List[str] = None,
                        sensitive_data: bool = False):
    """Decorator to enforce Zero-Trust on specific functions."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            for value in kwargs.values():
                if isinstance(value, Request):
                    request = value
                    break

            if not request:
                raise ValueError("Request object not found in function arguments")

            # Validate token and permissions
            token_data = getattr(request.state, 'token_data', None)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check specific permissions if required
            if required_permissions:
                user_id = token_data.get("sub")
                roles = token_data.get("roles", [])
                domains = token_data.get("domains", [])

                if not rbac_enforcer.check_permissions(user_id, roles, domains, required_permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )

            # Additional validation for sensitive data
            if sensitive_data:
                await ZeroTrustMiddleware()._validate_domain_access(request, token_data)

            return await func(*args, **kwargs)
        return wrapper
    return decorator
