"""BFOS monetization engines."""

from src.bfos.aoq_hook import optimize_fee, optimize_fx_timing, risk_adjustment
from src.bfos.accounting import generate_statement, merchant_accounting_engine, statement_engine
from src.bfos.fee_engine import (
    calculate_certified_statement_fee,
    calculate_diaspora_fee,
    calculate_internal_transfer_fee,
    calculate_tontine_fee,
    fee_engine,
)
from src.bfos.fx_engine import (
    convert_usd_to_cfa,
    fx_engine,
    get_current_rate,
    record_fx_transaction,
    validate_rate_integrity,
)
from src.bfos.revenue_engine import get_revenue_summary, record_revenue, revenue_engine
from src.bfos.tontine import tontine_engine

__all__ = [
    "fee_engine",
    "revenue_engine",
    "fx_engine",
    "calculate_internal_transfer_fee",
    "calculate_diaspora_fee",
    "calculate_certified_statement_fee",
    "calculate_tontine_fee",
    "record_revenue",
    "get_revenue_summary",
    "convert_usd_to_cfa",
    "get_current_rate",
    "validate_rate_integrity",
    "record_fx_transaction",
    "optimize_fee",
    "optimize_fx_timing",
    "risk_adjustment",
    "merchant_accounting_engine",
    "statement_engine",
    "generate_statement",
    "tontine_engine",
]
