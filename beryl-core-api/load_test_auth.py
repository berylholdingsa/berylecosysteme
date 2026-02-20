#!/usr/bin/env python3
"""
Load test script for Zero-Trust security metrics validation.
Tests authentication attempts, rejections, and success metrics.
"""

import asyncio
import aiohttp
import json
import base64
import time

# Configuration
BASE_URL = "http://localhost:8000"
CONCURRENT_REQUESTS = 10
TOTAL_REQUESTS = 100

# Test tokens
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

# Test scenarios
test_cases = [
    # Missing token
    {"endpoint": "/api/v1/fintech/payments", "headers": {}, "expected_status": 401},
    # Invalid token format
    {"endpoint": "/api/v1/fintech/payments", "headers": {"Authorization": "Bearer invalid"}, "expected_status": 401},
    # Valid fintech token
    {"endpoint": "/api/v1/fintech/payments", "headers": {"Authorization": f"Bearer {create_jwt_token(['fintech'])}"}, "expected_status": 404},  # 404 because endpoint not implemented
    # Invalid scope for fintech
    {"endpoint": "/api/v1/fintech/payments", "headers": {"Authorization": f"Bearer {create_jwt_token(['mobility'])}"}, "expected_status": 403},
    # Valid mobility token
    {"endpoint": "/api/v1/mobility/demand", "headers": {"Authorization": f"Bearer {create_jwt_token(['mobility'])}"}, "expected_status": 404},
    # Invalid scope for mobility
    {"endpoint": "/api/v1/mobility/demand", "headers": {"Authorization": f"Bearer {create_jwt_token(['fintech'])}"}, "expected_status": 403},
    # Valid ESG token
    {"endpoint": "/api/v1/esg/pedometer", "headers": {"Authorization": f"Bearer {create_jwt_token(['esg'])}"}, "expected_status": 404},
    # Valid social token
    {"endpoint": "/api/v1/social/feed", "headers": {"Authorization": f"Bearer {create_jwt_token(['social'])}"}, "expected_status": 404},
]

async def make_request(session, test_case):
    """Make a single request and return status."""
    try:
        async with session.get(f"{BASE_URL}{test_case['endpoint']}", headers=test_case['headers']) as response:
            return response.status
    except Exception as e:
        print(f"Request failed: {e}")
        return 500

async def run_load_test():
    """Run the load test."""
    print(f"Starting load test with {TOTAL_REQUESTS} requests, {CONCURRENT_REQUESTS} concurrent...")

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(TOTAL_REQUESTS):
            test_case = test_cases[i % len(test_cases)]
            tasks.append(make_request(session, test_case))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count results
    status_counts = {}
    for result in results:
        if isinstance(result, Exception):
            status = "error"
        else:
            status = result
        status_counts[status] = status_counts.get(status, 0) + 1

    print("Load test results:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")

    print("\nFetching metrics...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/metrics") as response:
            metrics = await response.text()

    # Parse and display relevant metrics
    lines = metrics.split('\n')
    print("\nSecurity Metrics:")
    for line in lines:
        if 'beryl_auth' in line and not line.startswith('#'):
            print(f"  {line}")

if __name__ == "__main__":
    asyncio.run(run_load_test())