# Backup and Recovery Procedure

- Database backup cadence: full daily + WAL/incremental every 5 minutes.
- Outbox table replayable for event delivery recovery.
- Recovery sequence:
  1. Restore DB to latest consistent point.
  2. Verify audit chain integrity.
  3. Run outbox publish replay.
  4. Confirm DLQ count and consumer lag return to baseline.
