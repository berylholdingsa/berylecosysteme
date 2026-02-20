"""Backend mobility ride lifecycle state machine and quote engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
from math import atan2, cos, radians, sin, sqrt
from threading import Lock
from typing import Any
from uuid import uuid4


class RideLifecycleError(RuntimeError):
    """Base ride lifecycle error with HTTP mapping metadata."""

    code = "MOBILITY_RIDE_ERROR"
    status_code = 400

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class RideQuoteNotFoundError(RideLifecycleError):
    code = "MOBILITY_QUOTE_NOT_FOUND"
    status_code = 404


class RideNotFoundError(RideLifecycleError):
    code = "MOBILITY_RIDE_NOT_FOUND"
    status_code = 404


class RideStateTransitionError(RideLifecycleError):
    code = "MOBILITY_RIDE_INVALID_STATE"
    status_code = 409


class RideIdempotencyConflictError(RideLifecycleError):
    code = "MOBILITY_IDEMPOTENCY_CONFLICT"
    status_code = 409


@dataclass(slots=True)
class QuoteRecord:
    quote_id: str
    rider_id: str
    pickup_label: str
    dropoff_label: str
    service_tier: str
    distance_km: float
    estimated_eta_minutes: int
    estimated_price_xof: int
    pricing_model_version: str
    confidence_interval: dict[str, int]
    explainability: dict[str, Any]
    co2_saved_kg: float
    expires_at: datetime
    created_at: datetime


class RideLifecycleService:
    """In-memory ride lifecycle kernel for contract-first backend APIs."""

    _pricing_model_version = "mobility-pricing-v2.0.0"

    def __init__(self) -> None:
        self._quotes: dict[str, QuoteRecord] = {}
        self._rides: dict[str, dict[str, Any]] = {}
        self._idempotency_results: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def quote_ride(
        self,
        *,
        rider_id: str,
        pickup_label: str,
        dropoff_label: str,
        service_tier: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        with self._lock:
            cached = self._idempotency_results.get(f"quote:{idempotency_key}")
            if cached is not None:
                return dict(cached)

            distance_km, demand_multiplier = self._estimate_distance_and_demand(
                pickup_label=pickup_label,
                dropoff_label=dropoff_label,
            )
            estimated_price_xof = self._estimate_price_xof(
                distance_km=distance_km,
                service_tier=service_tier,
                demand_multiplier=demand_multiplier,
            )
            eta_minutes = max(4, int(round(distance_km * 2.7 + 3)))
            confidence_margin = max(150, int(round(estimated_price_xof * 0.08)))
            confidence_interval = {
                "lower": max(0, estimated_price_xof - confidence_margin),
                "upper": estimated_price_xof + confidence_margin,
            }
            explainability = {
                "summary": (
                    f"Prix {service_tier} calculé via distance, niveau de demande et risque de route."
                ),
                "factors": [
                    {"name": "distance_km", "weight": 0.55, "value": distance_km},
                    {"name": "demand_multiplier", "weight": 0.30, "value": demand_multiplier},
                    {"name": "service_tier", "weight": 0.15, "value": service_tier},
                ],
            }

            now = datetime.now(tz=UTC)
            quote = QuoteRecord(
                quote_id=str(uuid4()),
                rider_id=rider_id,
                pickup_label=pickup_label,
                dropoff_label=dropoff_label,
                service_tier=service_tier,
                distance_km=distance_km,
                estimated_eta_minutes=eta_minutes,
                estimated_price_xof=estimated_price_xof,
                pricing_model_version=self._pricing_model_version,
                confidence_interval=confidence_interval,
                explainability=explainability,
                co2_saved_kg=round(distance_km * 0.13, 2),
                expires_at=now + timedelta(minutes=10),
                created_at=now,
            )
            self._quotes[quote.quote_id] = quote

            response = {
                "quote_id": quote.quote_id,
                "rider_id": quote.rider_id,
                "pickup_label": quote.pickup_label,
                "dropoff_label": quote.dropoff_label,
                "service_tier": quote.service_tier,
                "distance_km": quote.distance_km,
                "estimated_eta_minutes": quote.estimated_eta_minutes,
                "estimated_price_xof": quote.estimated_price_xof,
                "pricing_model_version": quote.pricing_model_version,
                "confidence_interval": quote.confidence_interval,
                "explainability": quote.explainability,
                "co2_saved_kg": quote.co2_saved_kg,
                "expires_at": quote.expires_at,
            }
            self._idempotency_results[f"quote:{idempotency_key}"] = dict(response)
            return response

    def book_ride(self, *, quote_id: str, rider_id: str, idempotency_key: str) -> dict[str, Any]:
        return self._transition(
            action="book",
            idempotency_key=idempotency_key,
            transition_fn=lambda: self._book_internal(quote_id=quote_id, rider_id=rider_id),
        )

    def assign_ride(self, *, ride_id: str, driver_id: str | None, idempotency_key: str) -> dict[str, Any]:
        return self._transition(
            action="assign",
            idempotency_key=idempotency_key,
            transition_fn=lambda: self._assign_internal(ride_id=ride_id, driver_id=driver_id),
        )

    def cancel_ride(self, *, ride_id: str, reason: str, idempotency_key: str) -> dict[str, Any]:
        return self._transition(
            action="cancel",
            idempotency_key=idempotency_key,
            transition_fn=lambda: self._cancel_internal(ride_id=ride_id, reason=reason),
        )

    def complete_ride(
        self,
        *,
        ride_id: str,
        distance_km: float | None,
        duration_minutes: int | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        return self._transition(
            action="complete",
            idempotency_key=idempotency_key,
            transition_fn=lambda: self._complete_internal(
                ride_id=ride_id,
                distance_km=distance_km,
                duration_minutes=duration_minutes,
            ),
        )

    def get_ride(self, *, ride_id: str) -> dict[str, Any]:
        with self._lock:
            ride = self._rides.get(ride_id)
            if ride is None:
                raise RideNotFoundError("Ride not found", {"ride_id": ride_id})
            return dict(ride)

    def _transition(
        self,
        *,
        action: str,
        idempotency_key: str,
        transition_fn,
    ) -> dict[str, Any]:
        cache_key = f"{action}:{idempotency_key}"
        with self._lock:
            cached = self._idempotency_results.get(cache_key)
            if cached is not None:
                return dict(cached)
            response = transition_fn()
            self._idempotency_results[cache_key] = dict(response)
            return response

    def _book_internal(self, *, quote_id: str, rider_id: str) -> dict[str, Any]:
        quote = self._quotes.get(quote_id)
        if quote is None:
            raise RideQuoteNotFoundError("Quote not found", {"quote_id": quote_id})
        if quote.expires_at <= datetime.now(tz=UTC):
            raise RideQuoteNotFoundError("Quote expired", {"quote_id": quote_id})
        if quote.rider_id != rider_id:
            raise RideLifecycleError(
                "Quote rider mismatch",
                {"quote_rider_id": quote.rider_id, "rider_id": rider_id},
            )

        now = datetime.now(tz=UTC)
        ride_id = str(uuid4())
        ride = {
            "ride_id": ride_id,
            "quote_id": quote.quote_id,
            "rider_id": quote.rider_id,
            "driver_id": None,
            "status": "BOOKED",
            "pickup_label": quote.pickup_label,
            "dropoff_label": quote.dropoff_label,
            "service_tier": quote.service_tier,
            "distance_km": quote.distance_km,
            "estimated_eta_minutes": quote.estimated_eta_minutes,
            "estimated_price_xof": quote.estimated_price_xof,
            "final_price_xof": None,
            "pricing_model_version": quote.pricing_model_version,
            "confidence_interval": quote.confidence_interval,
            "explainability": quote.explainability,
            "co2_saved_kg": quote.co2_saved_kg,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "cancellation_reason": None,
        }
        self._rides[ride_id] = ride
        return dict(ride)

    def _assign_internal(self, *, ride_id: str, driver_id: str | None) -> dict[str, Any]:
        ride = self._rides.get(ride_id)
        if ride is None:
            raise RideNotFoundError("Ride not found", {"ride_id": ride_id})
        if ride["status"] != "BOOKED":
            raise RideStateTransitionError(
                "Ride cannot be assigned from current state",
                {"ride_id": ride_id, "status": ride["status"]},
            )
        ride["driver_id"] = driver_id or f"driver-{uuid4().hex[:8]}"
        ride["status"] = "ASSIGNED"
        ride["updated_at"] = datetime.now(tz=UTC)
        return dict(ride)

    def _cancel_internal(self, *, ride_id: str, reason: str) -> dict[str, Any]:
        ride = self._rides.get(ride_id)
        if ride is None:
            raise RideNotFoundError("Ride not found", {"ride_id": ride_id})
        if ride["status"] not in {"BOOKED", "ASSIGNED"}:
            raise RideStateTransitionError(
                "Ride cannot be cancelled from current state",
                {"ride_id": ride_id, "status": ride["status"]},
            )
        ride["status"] = "CANCELLED"
        ride["cancellation_reason"] = reason
        ride["updated_at"] = datetime.now(tz=UTC)
        return dict(ride)

    def _complete_internal(
        self,
        *,
        ride_id: str,
        distance_km: float | None,
        duration_minutes: int | None,
    ) -> dict[str, Any]:
        ride = self._rides.get(ride_id)
        if ride is None:
            raise RideNotFoundError("Ride not found", {"ride_id": ride_id})
        if ride["status"] != "ASSIGNED":
            raise RideStateTransitionError(
                "Ride cannot be completed from current state",
                {"ride_id": ride_id, "status": ride["status"]},
            )

        effective_distance = distance_km if distance_km is not None else float(ride["distance_km"])
        effective_duration = duration_minutes if duration_minutes is not None else int(ride["estimated_eta_minutes"])
        surcharge_multiplier = 1.0 + min(0.20, max(0.0, (effective_duration - int(ride["estimated_eta_minutes"])) * 0.01))
        final_price = int(round(float(ride["estimated_price_xof"]) * surcharge_multiplier))

        ride["distance_km"] = round(effective_distance, 2)
        ride["estimated_eta_minutes"] = max(1, int(effective_duration))
        ride["status"] = "COMPLETED"
        ride["final_price_xof"] = max(final_price, int(ride["estimated_price_xof"]))
        ride["updated_at"] = datetime.now(tz=UTC)
        ride["completed_at"] = ride["updated_at"]
        return dict(ride)

    def _estimate_distance_and_demand(self, *, pickup_label: str, dropoff_label: str) -> tuple[float, float]:
        pickup_coords = self._parse_coordinates(pickup_label)
        dropoff_coords = self._parse_coordinates(dropoff_label)
        if pickup_coords is not None and dropoff_coords is not None:
            distance_km = self._haversine_distance_km(
                lat1=pickup_coords[0],
                lon1=pickup_coords[1],
                lat2=dropoff_coords[0],
                lon2=dropoff_coords[1],
            )
        else:
            seed = int(
                hashlib.sha256(f"{pickup_label}|{dropoff_label}".encode("utf-8")).hexdigest()[:8],
                16,
            )
            distance_km = 2.5 + ((seed % 230) / 20.0)
        distance_km = round(max(1.2, distance_km), 2)

        demand_seed = int(
            hashlib.sha256(f"demand:{pickup_label}:{dropoff_label}".encode("utf-8")).hexdigest()[:6],
            16,
        )
        demand_multiplier = round(1.0 + ((demand_seed % 14) / 100.0), 2)
        return distance_km, demand_multiplier

    @staticmethod
    def _parse_coordinates(label: str) -> tuple[float, float] | None:
        parts = [part.strip() for part in label.split(",")]
        if len(parts) != 2:
            return None
        try:
            lat = float(parts[0])
            lng = float(parts[1])
        except ValueError:
            return None
        if lat < -90 or lat > 90 or lng < -180 or lng > 180:
            return None
        return lat, lng

    @staticmethod
    def _haversine_distance_km(*, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r_km = 6371.0
        d_lat = radians(lat2 - lat1)
        d_lon = radians(lon2 - lon1)
        a = (
            sin(d_lat / 2.0) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2.0) ** 2
        )
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return r_km * c

    @classmethod
    def _estimate_price_xof(cls, *, distance_km: float, service_tier: str, demand_multiplier: float) -> int:
        tier = service_tier.lower().strip()
        base_fee = {
            "standard": 800,
            "comfort": 1200,
            "premium": 1800,
        }.get(tier, 800)
        per_km_fee = {
            "standard": 320,
            "comfort": 430,
            "premium": 560,
        }.get(tier, 320)
        raw_amount = (base_fee + distance_km * per_km_fee) * demand_multiplier
        return int(round(max(1200, raw_amount)))
