# Key Rotation Procedure

- JWT keys managed by `JwtRotationService` with grace period.
- Event HMAC and PSP webhook HMAC rotated via environment secret management.
- Rotation validation steps:
  1. Rotate key.
  2. Issue canary token/event.
  3. Verify acceptance of new key and planned expiry of old key.
  4. Confirm no signature validation failures spike.
