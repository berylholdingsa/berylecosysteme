"""AOQ routes for Beryl Core API."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.aoq_schema import (
    AuditTrailResponse,
    DecisionRequest,
    DecisionResponse,
    RuleResponse,
    RuleSchema,
    SignalRequest,
    SignalResponse,
)
from src.observability.logger import logger
from src.orchestration.aoq.service import AoqNotFoundError, AoqService, AoqValidationError


router = APIRouter()
service = AoqService()


@router.post("/signals", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
def create_signal(request: SignalRequest):
    try:
        payload = {
            "features": request.features.model_dump(),
            "metadata": request.metadata,
        }
        signal = service.create_signal(
            user_id=request.user_id,
            source=request.source,
            payload=payload,
        )
        return SignalResponse(
            signal_id=signal.id,
            user_id=signal.user_id,
            source=signal.source,
            created_at=signal.created_at,
        )
    except Exception as exc:
        logger.exception("event=aoq_signal_error user_id=%s", request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"{exc.__class__.__name__}: {exc}",
        ) from exc


@router.post("/decision", response_model=DecisionResponse)
def create_decision(request: DecisionRequest):
    try:
        decision = service.compute_decision(
            user_id=request.user_id,
            signal_id=request.signal_id,
            features_payload=request.features.model_dump() if request.features else None,
            metadata=request.metadata,
        )
        return DecisionResponse(
            decision_id=decision.decision_id,
            signal_id=decision.signal_id,
            rule_id=decision.rule_id,
            user_id=decision.user_id,
            score=decision.score,
            threshold=decision.threshold,
            decision=decision.decision,
            rationale=decision.rationale,
            created_at=decision.created_at,
        )
    except AoqValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AoqNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("event=aoq_decision_error user_id=%s", request.user_id)
        raise HTTPException(
            status_code=500,
            detail=f"{exc.__class__.__name__}: {exc}",
        ) from exc


@router.post("/evaluate", response_model=DecisionResponse)
def evaluate_decision(request: DecisionRequest):
    return create_decision(request)


@router.get("/rules", response_model=list[RuleResponse])
def list_rules():
    rules = service.list_rules()
    return [RuleResponse.model_validate(rule) for rule in rules]


@router.post("/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(request: RuleSchema):
    try:
        rule = service.create_rule(request.model_dump())
        return RuleResponse.model_validate(rule)
    except AoqValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("event=aoq_rule_error name=%s", request.name)
        raise HTTPException(status_code=500, detail="failed to create AOQ rule") from exc


@router.get("/decisions/{decision_id}", response_model=DecisionResponse)
def get_decision(decision_id: UUID):
    try:
        decision = service.get_decision(decision_id)
        return DecisionResponse(
            decision_id=decision.id,
            signal_id=decision.signal_id,
            rule_id=decision.rule_id,
            user_id=decision.user_id,
            score=decision.score,
            threshold=decision.threshold,
            decision=decision.decision,
            rationale=decision.rationale,
            created_at=decision.created_at,
        )
    except AoqNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("event=aoq_get_decision_error decision_id=%s", decision_id)
        raise HTTPException(status_code=500, detail="failed to fetch AOQ decision") from exc


@router.get("/audit/{entity_id}", response_model=list[AuditTrailResponse])
def get_audit(entity_id: str):
    try:
        entries = service.get_audit_trail(entity_id)
        return [AuditTrailResponse.model_validate(item) for item in entries]
    except Exception as exc:
        logger.exception("event=aoq_audit_fetch_error entity_id=%s", entity_id)
        raise HTTPException(status_code=500, detail="failed to fetch AOQ audit trail") from exc
