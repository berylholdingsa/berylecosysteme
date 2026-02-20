"""Centralized runtime settings loaded from environment variables."""

import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    model_config = ConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/beryl_db")

    # Security: JWT / cryptography
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-jwt-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_minutes: int = int(os.getenv("JWT_EXPIRATION_MINUTES", 60))
    jwt_signing_keys_json: str = os.getenv("JWT_SIGNING_KEYS_JSON", "")
    jwt_active_kid: str = os.getenv("JWT_ACTIVE_KID", "default")
    jwt_rotation_interval_minutes: int = int(os.getenv("JWT_ROTATION_INTERVAL_MINUTES", 1440))
    jwt_rotation_grace_minutes: int = int(os.getenv("JWT_ROTATION_GRACE_MINUTES", 120))
    bcrypt_rounds: int = int(os.getenv("BCRYPT_ROUNDS", 12))
    aes256_key_b64: str = os.getenv("AES256_KEY_B64", "")
    event_hmac_secret: str = os.getenv("EVENT_HMAC_SECRET", "change-me-event-hmac")
    psp_webhook_hmac_secret: str = os.getenv("PSP_WEBHOOK_HMAC_SECRET", "change-me-psp-hmac")

    # Security: request protection and transport
    correlation_id_required: bool = os.getenv("CORRELATION_ID_REQUIRED", "true").lower() == "true"
    nonce_ttl_seconds: int = int(os.getenv("NONCE_TTL_SECONDS", 300))
    nonce_max_skew_seconds: int = int(os.getenv("NONCE_MAX_SKEW_SECONDS", 300))
    enforce_tls: bool = os.getenv("ENFORCE_TLS", "false").lower() == "true"
    cors_allowed_origins: str = os.getenv("CORS_ALLOWED_ORIGINS", "https://app.beryl.local")
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", 120))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))

    # External APIs
    fintech_api_url: str = os.getenv("FINTECH_API_URL", "https://api.fintech.example.com")
    mobility_api_url: str = os.getenv("MOBILITY_API_URL", "https://api.mobility.example.com")
    esg_api_url: str = os.getenv("ESG_API_URL", "https://api.esg.example.com")
    social_api_url: str = os.getenv("SOCIAL_API_URL", "https://api.social.example.com")
    greenos_model_version: str = os.getenv("GREENOS_MODEL_VERSION", "greenos-co2-v1")
    greenos_methodology_id: str = os.getenv("GREENOS_METHODOLOGY_ID", "IPCC-ADEME-LOCAL-v1")
    greenos_country_factors_json: str = os.getenv(
        "GREENOS_COUNTRY_FACTORS_JSON",
        (
            '{"CI":{"thermal_factor_local":0.192,"ev_factor_local":0.054},'
            '"SN":{"thermal_factor_local":0.187,"ev_factor_local":0.061},'
            '"KE":{"thermal_factor_local":0.171,"ev_factor_local":0.032}}'
        ),
    )
    greenos_secret_provider: str = os.getenv("GREENOS_SECRET_PROVIDER", "env")
    greenos_secret_cache_ttl_seconds: float = float(os.getenv("GREENOS_SECRET_CACHE_TTL_SECONDS", 0))
    greenos_vault_addr: str = os.getenv("GREENOS_VAULT_ADDR", "")
    greenos_vault_token: str = os.getenv("GREENOS_VAULT_TOKEN", "")
    greenos_vault_path: str = os.getenv("GREENOS_VAULT_PATH", "secret/data/greenos")
    greenos_kms_key_id: str = os.getenv("GREENOS_KMS_KEY_ID", "")
    greenos_kms_provider: str = os.getenv("GREENOS_KMS_PROVIDER", "generic")
    greenos_kms_region: str = os.getenv("GREENOS_KMS_REGION", "")
    greenos_signing_secret: str = os.getenv("GREENOS_SIGNING_SECRET", "change-me-greenos-signing-secret")
    greenos_signing_active_key_version: str = os.getenv("GREENOS_SIGNING_ACTIVE_KEY_VERSION", "v1")
    greenos_signing_keys_json: str = os.getenv("GREENOS_SIGNING_KEYS_JSON", "{}")
    greenos_ed25519_private_key: str = os.getenv(
        "GREENOS_ED25519_PRIVATE_KEY",
        "y4RvmUHSyyFmAuuIL8g17LxPYLj/Kti53WN8bNyl4XU=",
    )
    greenos_ed25519_public_key: str = os.getenv(
        "GREENOS_ED25519_PUBLIC_KEY",
        "mVoiTw3s4D07BzqO1aE6IN4x+lfUzKhXjgPX0W03GL8=",
    )
    greenos_ed25519_active_key_version: str = os.getenv("GREENOS_ED25519_ACTIVE_KEY_VERSION", "v1")
    greenos_ed25519_private_keys_json: str = os.getenv("GREENOS_ED25519_PRIVATE_KEYS_JSON", "{}")
    greenos_ed25519_public_keys_json: str = os.getenv("GREENOS_ED25519_PUBLIC_KEYS_JSON", "{}")
    greenos_mrv_baseline_reference: str = os.getenv(
        "GREENOS_MRV_BASELINE_REFERENCE",
        "distance_km * thermal_factor_local baseline",
    )
    greenos_mrv_emission_factor_source: str = os.getenv(
        "GREENOS_MRV_EMISSION_FACTOR_SOURCE",
        "GREENOS_COUNTRY_FACTORS_JSON",
    )
    greenos_mrv_methodology_description: str = os.getenv(
        "GREENOS_MRV_METHODOLOGY_DESCRIPTION",
        "Avoided CO2 = distance_km * (thermal_factor_local - ev_factor_local).",
    )
    enable_outbox_worker: bool = os.getenv("ENABLE_OUTBOX_WORKER", "false").lower() == "true"
    greenos_outbox_poll_interval_seconds: float = float(os.getenv("GREENOS_OUTBOX_POLL_INTERVAL_SECONDS", 0.5))
    greenos_outbox_batch_size: int = int(os.getenv("GREENOS_OUTBOX_BATCH_SIZE", 100))
    greenos_outbox_max_retry_count: int = int(os.getenv("GREENOS_OUTBOX_MAX_RETRY_COUNT", 5))

    # Observability
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    tracing_enabled: bool = os.getenv("TRACING_ENABLED", "true").lower() == "true"
    jaeger_host: str = os.getenv("JAEGER_HOST", "localhost")
    jaeger_port: int = int(os.getenv("JAEGER_PORT", 14268))
    jaeger_endpoint: str = os.getenv("JAEGER_ENDPOINT", "")
    zipkin_endpoint: str = os.getenv("ZIPKIN_ENDPOINT", "")

    # Audit
    audit_enabled: bool = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
    audit_log_file: str = os.getenv("AUDIT_LOG_FILE", "logs/audit.log")
    audit_secret_key: str = os.getenv("AUDIT_SECRET_KEY", "change-me-audit-hmac")
    audit_chain_enabled: bool = os.getenv("AUDIT_CHAIN_ENABLED", "true").lower() == "true"

    # Compliance
    compliance_risk_threshold: float = float(os.getenv("COMPLIANCE_RISK_THRESHOLD", 70.0))
    compliance_transaction_amount_threshold: float = float(os.getenv("COMPLIANCE_TRANSACTION_AMOUNT_THRESHOLD", 10000.0))
    sanctions_list_path: str = os.getenv("SANCTIONS_LIST_PATH", "security/sanctions_list.json")

    # BFOS monetization
    bfos_internal_transfer_fee_rate: float = float(os.getenv("BFOS_INTERNAL_TRANSFER_FEE_RATE", 0.01))
    bfos_diaspora_fee_rate: float = float(os.getenv("BFOS_DIASPORA_FEE_RATE", 0.02))
    bfos_certified_statement_fee_rate: float = float(os.getenv("BFOS_CERTIFIED_STATEMENT_FEE_RATE", 0.01))
    bfos_tontine_fee_rate: float = float(os.getenv("BFOS_TONTINE_FEE_RATE", 0.01))
    bfos_fx_default_usd_xof_rate: float = float(os.getenv("BFOS_FX_DEFAULT_USD_XOF_RATE", 610.0))
    bfos_fx_fee_rate: float = float(os.getenv("BFOS_FX_FEE_RATE", 0.01))
    bfos_fx_margin_rate: float = float(os.getenv("BFOS_FX_MARGIN_RATE", 0.005))
    bfos_statement_currency: str = os.getenv("BFOS_STATEMENT_CURRENCY", "XOF")
    bfos_statement_verification_base_url: str = os.getenv(
        "BFOS_STATEMENT_VERIFICATION_BASE_URL",
        "/api/v1/fintech/statements",
    )
    bfos_statement_signing_algorithm: str = os.getenv("BFOS_STATEMENT_SIGNING_ALGORITHM", "ECDSA_SHA256")
    bfos_statement_signing_private_key_b64: str = os.getenv("BFOS_STATEMENT_SIGNING_PRIVATE_KEY_B64", "")
    bfos_tontine_max_members: int = int(os.getenv("BFOS_TONTINE_MAX_MEMBERS", 10))
    bfos_tontine_security_code_pepper: str = os.getenv("BFOS_TONTINE_SECURITY_CODE_PEPPER", "change-me-tontine-pepper")
    bfos_tontine_currency: str = os.getenv("BFOS_TONTINE_CURRENCY", "XOF")
    bfos_tontine_default_reputation_score: float = float(os.getenv("BFOS_TONTINE_DEFAULT_REPUTATION_SCORE", 50.0))
    bfos_tontine_late_penalty_rate: float = float(os.getenv("BFOS_TONTINE_LATE_PENALTY_RATE", 0.01))

    # Event bus
    event_bus_type: str = os.getenv("EVENT_BUS", "mock")  # mock, kafka, rabbitmq
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_consumer_topics: str = os.getenv(
        "KAFKA_CONSUMER_TOPICS",
        "fintech.transaction.completed,fintech.payment.failed,fintech.suspicious.activity",
    )
    kafka_consumer_group_prefix: str = os.getenv("KAFKA_CONSUMER_GROUP_PREFIX", "beryl-core")
    kafka_environment: str = os.getenv("KAFKA_ENVIRONMENT", os.getenv("ENVIRONMENT", "dev"))
    kafka_dlq_retention_ms: int = int(os.getenv("KAFKA_DLQ_RETENTION_MS", 604800000))
    kafka_manual_commit_only: bool = os.getenv("KAFKA_MANUAL_COMMIT_ONLY", "true").lower() == "true"
    kafka_required_signed_topics: str = os.getenv(
        "KAFKA_REQUIRED_SIGNED_TOPICS",
        "fintech.transaction.completed,fintech.payment.failed,fintech.suspicious.activity",
    )
    kafka_schema_registry_path: str = os.getenv("KAFKA_SCHEMA_REGISTRY_PATH", "config/event_schemas.json")

    # RabbitMQ settings (if using RabbitMQ event bus)
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "guest")

    # Legacy alias for backward compatibility
    env: str = environment

    @property
    def jwt_access_token_expire_minutes(self) -> int:
        """Backward-compatible alias for legacy naming."""
        return self.jwt_expiration_minutes

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        """Return strict CORS origins list."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def kafka_consumer_group(self) -> str:
        """Environment-scoped consumer group name."""
        normalized_env = "-".join(self.kafka_environment.strip().lower().split())
        return f"{self.kafka_consumer_group_prefix.strip().lower()}-{normalized_env}"

    @property
    def kafka_required_signed_topics_set(self) -> set[str]:
        return {topic.strip() for topic in self.kafka_required_signed_topics.split(",") if topic.strip()}


settings = Settings()
