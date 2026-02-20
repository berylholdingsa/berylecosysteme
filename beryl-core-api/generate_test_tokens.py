#!/usr/bin/env python3
"""
JWT Token Generator for Zero-Trust Validation Tests.
Generates valid JWT tokens with different scopes for Swagger testing.
"""

import json
import base64
import time

def create_jwt_token(scopes, domain="test", user_id="test-user"):
    """Create a simple JWT-like token for testing."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "domain": domain,
        "scopes": scopes,
        "exp": int(time.time()) + 3600
    }
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = "dummy_signature"  # Not verified in middleware
    return f"{header_b64}.{payload_b64}.{signature}"

if __name__ == "__main__":
    print("=== JWT Tokens for Zero-Trust Validation ===")
    print()

    # Token with fintech scope
    fintech_token = create_jwt_token(["fintech"], "fintech", "user-fintech")
    print("Fintech Token (scope: fintech):")
    print(f"Bearer {fintech_token}")
    print()

    # Token with mobility scope
    mobility_token = create_jwt_token(["mobility"], "mobility", "user-mobility")
    print("Mobility Token (scope: mobility):")
    print(f"Bearer {mobility_token}")
    print()

    # Token with ESG scope
    esg_token = create_jwt_token(["esg"], "esg", "user-esg")
    print("ESG Token (scope: esg):")
    print(f"Bearer {esg_token}")
    print()

    # Token with social scope
    social_token = create_jwt_token(["social"], "social", "user-social")
    print("Social Token (scope: social):")
    print(f"Bearer {social_token}")
    print()

    # Token with admin scope
    admin_token = create_jwt_token(["admin"], "admin", "user-admin")
    print("Admin Token (scope: admin):")
    print(f"Bearer {admin_token}")
    print()

    # Invalid scope token (for testing 403)
    invalid_scope_token = create_jwt_token(["invalid"], "invalid", "user-invalid")
    print("Invalid Scope Token (scope: invalid):")
    print(f"Bearer {invalid_scope_token}")
    print()

    print("=== Instructions ===")
    print("1. Copy the token above the 'Bearer ' prefix")
    print("2. In Swagger UI, click 'Authorize' button")
    print("3. Paste the token in the 'Value' field")
    print("4. Click 'Authorize' and 'Close'")
    print("5. Test the endpoints - they should now show security lock icons")