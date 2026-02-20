# OPA/Rego Policies for Zero-Trust Authorization
# This file defines authorization policies for the Beryl Core API Gateway

package beryl.authz

# Default deny
default allow = false

# Input structure expected:
# {
#   "user": {
#     "sub": "user-id",
#     "domain": "fintech|mobility|esg|social",
#     "scopes": ["fintech", "read"]
#   },
#   "request": {
#     "method": "GET|POST|PUT|DELETE",
#     "path": "/api/v1/fintech/payments",
#     "domain": "fintech"
#   }
# }

# Allow if user has required scope for domain
allow {
    required_scope := get_required_scope(input.request.path)
    required_scope != ""
    required_scope == input.user.domain
    scope_matches := {s | s := input.user.scopes[_]; s == required_scope}
    count(scope_matches) > 0
}

# Allow healthcheck and metrics endpoints
allow {
    input.request.path == "/health"
}

allow {
    input.request.path == "/metrics"
}

# Get required scope based on path
get_required_scope(path) = scope {
    path_parts := split(path, "/")
    count(path_parts) >= 3
    domain := path_parts[2]

    scope := domain
    domain == "fintech"
}

get_required_scope(path) = scope {
    path_parts := split(path, "/")
    count(path_parts) >= 3
    domain := path_parts[2]

    scope := domain
    domain == "mobility"
}

get_required_scope(path) = scope {
    path_parts := split(path, "/")
    count(path_parts) >= 3
    domain := path_parts[2]

    scope := domain
    domain == "esg"
}

get_required_scope(path) = scope {
    path_parts := split(path, "/")
    count(path_parts) >= 3
    domain := path_parts[2]

    scope := domain
    domain == "social"
}

# Default empty scope for unknown paths
get_required_scope(path) = "" {
    true
}

# Additional policies can be added here
# Example: Time-based access control
allow {
    required_scope := get_required_scope(input.request.path)
    required_scope != ""
    scope_matches := {s | s := input.user.scopes[_]; s == required_scope}
    count(scope_matches) > 0

    # Allow only during business hours (example)
    now := time.now_ns()
    business_start := time.parse_rfc3339_ns("09:00:00Z")
    business_end := time.parse_rfc3339_ns("17:00:00Z")

    hour := time.clock(now)[0]
    hour >= 9
    hour <= 17
}

# Admin scope for all domains
allow {
    input.user.scopes[_] == "admin"
}

# Audit logging policy
audit_decision = {
    "user_id": input.user.sub,
    "domain": input.user.domain,
    "path": input.request.path,
    "method": input.request.method,
    "allowed": allow,
    "timestamp": time.now_ns(),
    "required_scope": get_required_scope(input.request.path)
}