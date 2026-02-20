# API Contracts

## Version 1 (v1)

### Authentication

- POST /api/v1/auth/login
- POST /api/v1/auth/logout

### Fintech

- GET /api/v1/fintech/payments
- POST /api/v1/fintech/transactions

### Mobility

- GET /api/v1/mobility/demand
- POST /api/v1/mobility/routing

### ESG

- GET /api/v1/esg/health-data
- GET /api/v1/esg/esg-metrics

### Social

- GET /api/v1/social/recommendations
- POST /api/v1/social/moderate

TODO: Detail API contracts with request/response schemas.
---

## 🚗 Mobilité Électrique - API Contracts

### Demand Prediction

**Endpoint**: `POST /api/v1/mobility/demand/predict`

**Request Schema**:
```json
{
  "location": "string (required)",
  "time_window": "string (default: 'hourly')",
  "forecast_horizon": "integer (default: 24)"
}
```

**Response Schema** (200 OK):
```json
{
  "location": "string",
  "predicted_demand": "float",
  "confidence": "float (0-1)",
  "time_window": "string",
  "forecast_horizon": "integer",
  "forecast_data": [
    {
      "hour": "integer",
      "demand": "float"
    }
  ],
  "timestamp": "ISO 8601 datetime"
}
```

**Error Responses**:
- `422 Unprocessable Entity`: Invalid request schema
- `500 Internal Server Error`: Prediction failed

---

### Route Optimization

**Endpoint**: `POST /api/v1/mobility/routing/optimize`

**Request Schema**:
```json
{
  "origin": "string (required)",
  "destination": "string (required)",
  "vehicle_type": "string (enum: ebike, escooter, ecar)",
  "battery_level": "float (0-100, optional)",
  "max_time_minutes": "integer (optional)"
}
```

**Response Schema** (200 OK):
```json
{
  "route_id": "string",
  "origin": "string",
  "destination": "string",
  "vehicle_type": "string",
  "distance_km": "float",
  "estimated_time_minutes": "integer",
  "energy_consumption_kwh": "float",
  "waypoints": [
    {
      "lat": "float",
      "lng": "float"
    }
  ],
  "efficiency_score": "float (0-1)",
  "timestamp": "ISO 8601 datetime"
}
```

---

### Fleet Analysis

**Endpoint**: `POST /api/v1/mobility/fleet/{fleet_id}/analyze`

**Path Parameters**:
- `fleet_id`: string (required)

**Request Body**:
```json
{
  "fleet_id": "string (required)",
  "metrics": ["array of strings (optional)"]
}
```

**Response Schema** (200 OK):
```json
{
  "fleet_id": "string",
  "total_vehicles": "integer",
  "active_vehicles": "integer",
  "utilization_rate": "float (0-100)",
  "avg_battery_health": "float (0-100)",
  "maintenance_alerts": [
    {
      "vehicle_id": "string",
      "component": "string",
      "priority": "enum: low, medium, high, critical"
    }
  ],
  "key_insights": ["array of strings"],
  "recommendations": ["array of strings"],
  "timestamp": "ISO 8601 datetime"
}
```

---

### Vehicle Status

**Endpoint**: `GET /api/v1/mobility/vehicle/{vehicle_id}/status`

**Path Parameters**:
- `vehicle_id`: string (required)

**Response Schema** (200 OK):
```json
{
  "vehicle_id": "string",
  "vehicle_type": "string (enum: ebike, escooter, ecar)",
  "status": "enum: available, in_use, maintenance, offline",
  "battery_level": "float (0-100)",
  "location": {
    "lat": "float",
    "lng": "float"
  },
  "available": "boolean",
  "last_updated": "ISO 8601 datetime"
}
```

---

### Maintenance Prediction

**Endpoint**: `GET /api/v1/mobility/vehicle/{vehicle_id}/maintenance`

**Path Parameters**:
- `vehicle_id`: string (required)

**Response Schema** (200 OK):
```json
{
  "vehicle_id": "string",
  "maintenance_needed": "boolean",
  "priority": "enum: low, medium, high, critical",
  "predicted_failure_component": "string (nullable)",
  "recommended_action": "string",
  "days_until_maintenance": "integer (nullable)",
  "timestamp": "ISO 8601 datetime"
}
```

---

### Fleet Distribution Optimization

**Endpoint**: `POST /api/v1/mobility/fleet/{fleet_id}/optimize-distribution`

**Path Parameters**:
- `fleet_id`: string (required)

**Request Body**:
```json
{
  "fleet_id": "string (required)",
  "target_locations": ["array of strings (required)"]
}
```

**Response Schema** (200 OK):
```json
{
  "fleet_id": "string",
  "timestamp": "ISO 8601 datetime",
  "current_state": {
    "total_vehicles": "integer",
    "active_vehicles": "integer",
    "utilization_rate": "float"
  },
  "demand_forecast": [
    {
      "location": "string",
      "predicted_demand": "float"
    }
  ],
  "recommendations": ["array of strings"]
}
```

---

## Error Handling

All endpoints follow the same error response format:

```json
{
  "detail": "string (human-readable error message)"
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error / API unreachable

---

## Rate Limiting

- No explicit rate limiting configured (future enhancement)
- Clients should implement exponential backoff for retries
- Timeout: 30 seconds per request

---

## Authentication

Currently no authentication required (future integration with auth middleware).
All routes are accessible without JWT token.

---

## CORS

CORS enabled for all origins (configurable via FastAPI middleware).

