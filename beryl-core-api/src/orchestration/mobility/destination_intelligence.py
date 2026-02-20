"""
Destination Intelligence workflow for mobility.

This workflow keeps all mobility AOQ decision logic in backend:
- smart destination ranking
- dispatch recommendation
- mobility + ESG scoring
- simulation preview
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from math import ceil
from typing import Iterable

from src.api.v1.schemas.mobility_schema import DestinationHistoryItem
from src.observability.logger import logger


class MobilityDestinationValidationError(ValueError):
    """Raised when destination intelligence request data is invalid."""


@dataclass(slots=True)
class DestinationAlternativeResult:
    destination: str
    confidence: float
    score: float


@dataclass(slots=True)
class DestinationAoqResult:
    mobility_score: float
    esg_score: float
    dispatch_recommendation: str
    decision: str
    rationale: str


@dataclass(slots=True)
class DestinationSimulationResult:
    route_id: str
    distance_km: float
    estimated_time_minutes: int
    estimated_price_xof: int
    energy_kwh: float
    co2_saved_kg: float


@dataclass(slots=True)
class DestinationIntelligenceResult:
    selected_destination: str
    confidence: float
    alternatives: list[DestinationAlternativeResult]
    aoq: DestinationAoqResult
    simulation: DestinationSimulationResult
    timestamp: datetime


class DestinationIntelligenceWorkflow:
    """Backend-only AOQ workflow for intelligent mobility destination selection."""

    def evaluate(
        self,
        *,
        user_id: str,
        origin: str,
        query: str,
        candidate_destinations: list[str],
        trip_history: list[DestinationHistoryItem],
        travel_mode: str,
        traffic_level: str,
        weather_risk: str,
        battery_level: float | None,
        is_recurring: bool,
        hour_of_day: int | None,
    ) -> DestinationIntelligenceResult:
        logger.info(
            "event=mobility_destination_intelligence_compute user_id=%s origin=%s travel_mode=%s traffic=%s",
            user_id,
            origin,
            travel_mode,
            traffic_level,
        )

        candidates = self._collect_candidates(query, candidate_destinations, trip_history)
        history_counts = self._history_counts(trip_history)
        hour = datetime.now(UTC).hour if hour_of_day is None else hour_of_day

        scored = [
            self._score_candidate(
                query=query,
                destination=destination,
                history_count=history_counts.get(destination.lower(), 0),
                is_recurring=is_recurring,
                hour_of_day=hour,
                traffic_level=traffic_level,
                weather_risk=weather_risk,
            )
            for destination in candidates
        ]
        scored.sort(key=lambda item: item.score, reverse=True)

        selected = scored[0]
        simulation = self._build_simulation(
            origin=origin,
            destination=selected.destination,
            travel_mode=travel_mode,
            traffic_level=traffic_level,
            battery_level=battery_level,
        )
        aoq = self._build_aoq_result(
            confidence=selected.confidence,
            simulation=simulation,
            traffic_level=traffic_level,
            weather_risk=weather_risk,
            battery_level=battery_level,
        )

        return DestinationIntelligenceResult(
            selected_destination=selected.destination,
            confidence=selected.confidence,
            alternatives=scored[:3],
            aoq=aoq,
            simulation=simulation,
            timestamp=datetime.now(UTC),
        )

    def _collect_candidates(
        self,
        query: str,
        candidate_destinations: Iterable[str],
        trip_history: list[DestinationHistoryItem],
    ) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()

        def push(value: str) -> None:
            normalized = value.strip()
            if not normalized:
                return
            key = normalized.lower()
            if key in seen:
                return
            seen.add(key)
            ordered.append(normalized)

        push(query)
        for candidate in candidate_destinations:
            push(candidate)
        for item in trip_history:
            push(item.destination)

        if not ordered:
            raise MobilityDestinationValidationError(
                "at least one destination candidate must be provided"
            )
        return ordered

    def _history_counts(self, trip_history: list[DestinationHistoryItem]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in trip_history:
            key = item.destination.strip().lower()
            if not key:
                continue
            counts[key] = counts.get(key, 0) + int(item.count)
        return counts

    def _score_candidate(
        self,
        *,
        query: str,
        destination: str,
        history_count: int,
        is_recurring: bool,
        hour_of_day: int,
        traffic_level: str,
        weather_risk: str,
    ) -> DestinationAlternativeResult:
        query_key = query.strip().lower()
        destination_key = destination.strip().lower()

        query_match = 0.42 if destination_key == query_key else 0.28
        history_score = min(history_count / 8.0, 1.0) * 0.32
        recurring_bonus = 0.12 if is_recurring and history_count >= 2 else 0.0
        time_bonus = self._time_affinity_bonus(destination_key, hour_of_day)

        traffic_penalty = 0.0
        if traffic_level == "high":
            traffic_penalty = 0.10
        elif traffic_level == "moderate":
            traffic_penalty = 0.04

        weather_penalty = 0.06 if weather_risk == "high" else 0.0

        score = query_match + history_score + recurring_bonus + time_bonus - traffic_penalty - weather_penalty
        bounded_score = max(0.05, min(0.99, score))
        confidence = round(bounded_score, 4)
        score_value = round(bounded_score, 4)
        return DestinationAlternativeResult(
            destination=destination,
            confidence=confidence,
            score=score_value,
        )

    def _time_affinity_bonus(self, destination_key: str, hour_of_day: int) -> float:
        morning_keywords = ("bureau", "office", "work", "ecole", "school")
        evening_keywords = ("maison", "home", "residence")

        if 6 <= hour_of_day <= 10 and any(token in destination_key for token in morning_keywords):
            return 0.10
        if 17 <= hour_of_day <= 22 and any(token in destination_key for token in evening_keywords):
            return 0.10
        return 0.03

    def _build_simulation(
        self,
        *,
        origin: str,
        destination: str,
        travel_mode: str,
        traffic_level: str,
        battery_level: float | None,
    ) -> DestinationSimulationResult:
        seed = f"{origin}|{destination}"
        digest = int(sha256(seed.encode("utf-8")).hexdigest()[:8], 16)
        route_id = f"R{digest % 10000:04d}"

        distance_km = round(3.0 + ((digest % 220) / 10.0), 1)
        traffic_factor = {"low": 1.0, "moderate": 1.22, "high": 1.45}[traffic_level]
        eta_minutes = int(ceil(distance_km * 2.1 * traffic_factor))

        mode_energy_factor = {"solo": 0.13, "family": 0.17, "eco": 0.10}[travel_mode]
        if battery_level is not None and battery_level < 25:
            mode_energy_factor *= 0.95

        energy_kwh = round(distance_km * mode_energy_factor * (1.1 if traffic_level == "high" else 1.0), 2)
        estimated_price_xof = int(round(1200 + distance_km * 270 * traffic_factor))

        baseline_thermal_kwh = distance_km * 0.20
        co2_saved_kg = round(max(0.0, baseline_thermal_kwh - energy_kwh), 2)

        return DestinationSimulationResult(
            route_id=route_id,
            distance_km=distance_km,
            estimated_time_minutes=eta_minutes,
            estimated_price_xof=estimated_price_xof,
            energy_kwh=energy_kwh,
            co2_saved_kg=co2_saved_kg,
        )

    def _build_aoq_result(
        self,
        *,
        confidence: float,
        simulation: DestinationSimulationResult,
        traffic_level: str,
        weather_risk: str,
        battery_level: float | None,
    ) -> DestinationAoqResult:
        baseline_thermal_kwh = simulation.distance_km * 0.20
        if baseline_thermal_kwh <= 0:
            esg_score = 0.0
        else:
            esg_score = round(
                max(0.0, min(100.0, (simulation.co2_saved_kg / baseline_thermal_kwh) * 100.0)),
                2,
            )

        eta_score = max(0.0, 100.0 - (simulation.estimated_time_minutes * 2.0))
        confidence_score = confidence * 100.0
        traffic_score = {"low": 90.0, "moderate": 72.0, "high": 54.0}[traffic_level]
        battery_score = 70.0 if battery_level is None else battery_level

        mobility_score = round(
            (0.35 * eta_score)
            + (0.30 * confidence_score)
            + (0.20 * traffic_score)
            + (0.15 * battery_score),
            2,
        )
        mobility_score = max(0.0, min(100.0, mobility_score))

        if weather_risk == "high":
            dispatch = "safety_mode"
        elif traffic_level == "high" and simulation.estimated_time_minutes >= 30:
            dispatch = "pre_dispatch"
        elif mobility_score >= 80 and battery_score >= 40:
            dispatch = "priority_dispatch"
        else:
            dispatch = "normal_dispatch"

        if mobility_score >= 75 and esg_score >= 50:
            decision = "APPROVE"
        elif mobility_score >= 55:
            decision = "REVIEW"
        else:
            decision = "DEFER"

        rationale = (
            f"mobility_score={mobility_score:.2f};"
            f"esg_score={esg_score:.2f};"
            f"dispatch={dispatch};"
            f"traffic={traffic_level};"
            f"weather={weather_risk}"
        )
        return DestinationAoqResult(
            mobility_score=mobility_score,
            esg_score=esg_score,
            dispatch_recommendation=dispatch,
            decision=decision,
            rationale=rationale,
        )
