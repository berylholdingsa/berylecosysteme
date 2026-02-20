from __future__ import annotations

from src.compliance.transaction_risk_scorer import transaction_risk_scorer
from src.infrastructure.kafka.compliance.message_integrity_validator import MessageIntegrityValidator
from src.infrastructure.kafka.compliance.schema_registry_validator import SchemaValidationError, SchemaRegistryValidator


def test_risk_scorer_flags_high_amount() -> None:
    assessment = transaction_risk_scorer.assess(actor_id="user-1", amount=1_000_000.0, currency="XOF")
    assert assessment.score >= 25.0
    assert "high_amount_threshold" in assessment.reasons


def test_schema_validator_rejects_missing_required_fields(tmp_path) -> None:
    schema_file = tmp_path / "schemas.json"
    schema_file.write_text(
        '{"fintech.transaction.completed":{"required":["event_id","amount"],"field_types":{"event_id":"str","amount":"float"}}}',
        encoding="utf-8",
    )
    validator = SchemaRegistryValidator(registry_path=str(schema_file))

    try:
        validator.validate(topic="fintech.transaction.completed", payload={"event_id": "evt-1"})
        assert False, "schema validation should fail"
    except SchemaValidationError:
        assert True


def test_message_integrity_hash_roundtrip() -> None:
    validator = MessageIntegrityValidator()
    payload = {"event_id": "evt-1", "amount": 10.5}
    enriched = validator.enrich_with_hash(payload)
    assert validator.verify_hash(enriched)
