# 🚗 Intégration Mobilité Électrique (beryl-ai-engine)

## Vue d'ensemble

Cette documentation décrit l'intégration complète de **beryl-ai-engine** (intelligence de mobilité électrique) dans **beryl-core-api**, la couche d'orchestration centrale du Béryl Ecosystem.

## Architecture

### Stack Technologique
- **Framework**: FastAPI (Python 3.11+)
- **HTTP Async**: httpx
- **Validation**: Pydantic v2
- **Logging**: Python logging structuré

### Composants

#### 1. **MobilityAIClient** (`adapters/mobility_ai_engine/client.py`)
Client HTTP asynchrone qui communique avec beryl-ai-engine.

**Responsabilités**:
- Appels HTTP asynchrones vers beryl-ai-engine
- Gestion des timeouts (30s par défaut)
- Retry logique en cas d'erreur
- Logging de tous les appels

**Méthodes principales**:
```python
async def predict_demand(location, time_window, forecast_horizon)
async def optimize_route(origin, destination, vehicle_type, constraints)
async def analyze_fleet(fleet_id, metrics)
async def get_vehicle_status(vehicle_id)
async def predict_maintenance(vehicle_id)
```

#### 2. **MobilityMapper** (`adapters/mobility_ai_engine/mapper.py`)
Normalisateur de données qui transforme les réponses brutes en modèles de domaine.

**Modèles Pydantic**:
- `DemandPrediction`: Prédictions de demande avec intervalles de confiance
- `OptimizedRoute`: Routes optimisées avec métriques d'efficacité énergétique
- `FleetAnalysis`: Analyses de flotte avec insights et recommandations
- `VehicleStatus`: États de véhicules en temps réel
- `MaintenancePrediction`: Prédictions de maintenance avec priorités

#### 3. **FleetIntelligenceWorkflow** (`orchestration/mobility/fleet_intelligence.py`)
Orchestrateur qui coordonne les opérations de mobilité.

**Responsabilités**:
- Coordonner appels au client et au mapper
- Implémenter la logique métier de mobilité
- Logger les événements critiques
- Agréger et normaliser les réponses

**Workflows**:
- **Prédiction de demande**: Prédit la demande par localisation et horizon temporel
- **Optimisation de routes**: Optimise routes pour efficacité énergétique
- **Analyse de flotte**: Analyse l'état général et santé de la flotte
- **État véhicule**: Récupère l'état en temps réel
- **Prédiction maintenance**: Prédit les besoins de maintenance
- **Distribution de flotte**: Optimise la répartition des véhicules

#### 4. **Routes FastAPI** (`api/v1/routes/mobility_routes.py`)
Points d'entrée HTTP pour les opérations de mobilité.

**Endpoints**:
```
POST   /api/v1/mobility/demand/predict
POST   /api/v1/mobility/routing/optimize
POST   /api/v1/mobility/fleet/{fleet_id}/analyze
GET    /api/v1/mobility/vehicle/{vehicle_id}/status
GET    /api/v1/mobility/vehicle/{vehicle_id}/maintenance
POST   /api/v1/mobility/fleet/{fleet_id}/optimize-distribution
```

## Flux de Données

```
┌─────────────────────────────────────────────────────────────┐
│ Client Externe (Frontend/Partner API)                        │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼ HTTP Request
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Route Handler (mobility_routes.py)                   │
│ - Validation Pydantic                                        │
│ - Gestion d'erreurs HTTP                                     │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼ Appel orchestration
┌─────────────────────────────────────────────────────────────┐
│ FleetIntelligenceWorkflow                                    │
│ - Orchestration logique métier                               │
│ - Logging structuré                                          │
│ - Coordonner client + mapper                                 │
└───────────────┬─────────────────────┬──────────────────────┘
                │                     │
                ▼ Appel client        ▼ Map response
┌────────────────────────┐  ┌─────────────────────────────────┐
│ MobilityAIClient       │  │ MobilityMapper                  │
│ - HTTP async           │  │ - Normalize données             │
│ - Timeout/Retry        │  │ - Validation domaine            │
│ - Error handling       │  │ - Pydantic models               │
└────────────────────────┘  └─────────────────────────────────┘
                │
                ▼ HTTP Call
┌─────────────────────────────────────────────────────────────┐
│ beryl-ai-engine API                                          │
│ - Demand prediction engine                                   │
│ - Route optimization ML models                               │
│ - Fleet intelligence analytics                               │
└─────────────────────────────────────────────────────────────┘
```

## Schémas de Données

### DemandRequest / DemandResponse
```python
# Request
{
    "location": "Paris-Center",
    "time_window": "hourly",  # hourly|daily|weekly
    "forecast_horizon": 24
}

# Response
{
    "location": "Paris-Center",
    "predicted_demand": 150.5,
    "confidence": 0.92,
    "time_window": "hourly",
    "forecast_horizon": 24,
    "forecast_data": [
        {"hour": 0, "demand": 45.2},
        ...
    ],
    "timestamp": "2026-01-03T18:01:27.761Z"
}
```

### RouteRequest / RouteResponse
```python
# Request
{
    "origin": "Paris-Gare-du-Nord",
    "destination": "Paris-LaDefense",
    "vehicle_type": "ebike",  # ebike|escooter|ecar
    "battery_level": 85.0,    # optionnel
    "max_time_minutes": 30    # optionnel
}

# Response
{
    "route_id": "route_abc123",
    "origin": "Paris-Gare-du-Nord",
    "destination": "Paris-LaDefense",
    "vehicle_type": "ebike",
    "distance_km": 12.5,
    "estimated_time_minutes": 28,
    "energy_consumption_kwh": 0.45,
    "waypoints": [
        {"lat": 48.8806, "lng": 2.3553},
        ...
    ],
    "efficiency_score": 0.87,
    "timestamp": "2026-01-03T18:01:27.761Z"
}
```

### FleetAnalysisRequest / FleetAnalysisResponse
```python
# Request
{
    "fleet_id": "fleet_paris_001",
    "metrics": ["utilization", "battery_health"]  # optionnel
}

# Response
{
    "fleet_id": "fleet_paris_001",
    "total_vehicles": 250,
    "active_vehicles": 198,
    "utilization_rate": 79.2,
    "avg_battery_health": 89.5,
    "maintenance_alerts": [
        {
            "vehicle_id": "vehicle_123",
            "component": "battery",
            "priority": "high"
        }
    ],
    "key_insights": [
        "Peak demand expected 16:00-19:00",
        "Battery degradation 12% above threshold"
    ],
    "recommendations": [
        "Reposition 20 vehicles to downtown",
        "Schedule maintenance for 15 vehicles"
    ],
    "timestamp": "2026-01-03T18:01:27.761Z"
}
```

## Gestion d'Erreurs

### Patterns d'erreurs

**Erreurs d'API externe**:
```python
try:
    response = await self.client.predict_demand(...)
except Exception as e:
    logger.error(f"Demand prediction failed: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to predict demand"
    )
```

**Validation Pydantic**:
- Validations automatiques de requête
- Réponses 422 Unprocessable Entity si schéma invalide

## Configuration

### Variables d'environnement (`src/config/settings.py`)
```env
MOBILITY_API_URL=https://api.mobility.example.com
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ENV=development
LOG_LEVEL=INFO
```

## Scalabilité et Performance

### Async/Await
- Tous les appels API utilisent `httpx.AsyncClient`
- Pas de blocking I/O
- Support des connexions concurrentes

### Timeout
- Timeout par défaut: 30 secondes
- Configurable via `MobilityAIClient(timeout=60)`

### Logging
- Logs structurés pour tous les événements clés
- Logging d'erreurs avec context complet
- Sortie sur stdout pour containerisation

## Intégration avec d'autres branches

### Fintech Branch
- Routes de mobilité peuvent déclencher des transactions (ex: paiement de trajet)

### ESG Branch
- Données de mobilité contribuent aux métriques de durabilité

### Social Branch
- Recommandations basées sur patterns de mobilité utilisateurs

## Testing

### Unit Tests
```bash
pytest tests/unit/adapters/test_mobility_client.py
pytest tests/unit/orchestration/test_fleet_intelligence.py
```

### Integration Tests
```bash
pytest tests/integration/test_mobility_routes.py
```

## Maintenance Future

### Améliorations prévues
1. **Caching Redis**: Cache prédictions de demande (TTL 1h)
2. **WebSockets**: Notifications temps réel sur changements de flotte
3. **Prometheus**: Métriques d'appels API et latences
4. **Circuit Breaker**: Résilience aux pannes de beryl-ai-engine
5. **Rate Limiting**: Limites par client/utilisateur
6. **Batch Operations**: Endpoint pour analyses de flotte en batch

## Contacts et Support

Pour questions ou problèmes:
- Architecture: Équipe Backend
- ML/Intelligence: Équipe AI
- Déploiement: DevOps
