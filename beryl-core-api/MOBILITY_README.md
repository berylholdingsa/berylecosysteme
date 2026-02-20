# 🚗 Intégration Mobilité Électrique (beryl-ai-engine)

## 📌 Vue d'ensemble

Ce module intègre **beryl-ai-engine** (service d'intelligence mobilité électrique) dans **beryl-core-api**.

Il fournit une orchestration centralisée pour:
- 🎯 **Prédiction de demande** - Prédit la demande par localisation
- 🗺️ **Optimisation de routes** - Optimise routes pour efficacité énergétique
- 📊 **Analyse de flotte** - Analyse l'état et santé de la flotte
- 🔋 **Status véhicule** - État en temps réel des véhicules
- 🔧 **Prédiction maintenance** - Prédit les besoins de maintenance
- 📍 **Distribution optimale** - Répartit optimalement les véhicules

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│  Client (Frontend / Partner API)    │
└────────────────┬────────────────────┘
                 │
                 ▼ HTTP
┌─────────────────────────────────────┐
│  FastAPI Routes (mobility_routes.py)│
│  - Validation Pydantic              │
│  - HTTP error handling              │
└────────────────┬────────────────────┘
                 │
                 ▼ Python Call
┌─────────────────────────────────────┐
│  FleetIntelligenceWorkflow          │
│  - Orchestration métier             │
│  - Logging et monitoring            │
└────────┬─────────────────────┬──────┘
         │                     │
         ▼ API Call           ▼ Map Response
┌──────────────────────┐   ┌────────────────────┐
│  MobilityAIClient    │   │  MobilityMapper    │
│  - HTTP async        │   │  - Normalize data  │
│  - Retry logic       │   │  - Pydantic models │
└──────────────────────┘   └────────────────────┘
         │
         ▼ HTTP
┌─────────────────────────────────────┐
│  beryl-ai-engine (External API)     │
└─────────────────────────────────────┘
```

## 📁 Structure des fichiers

```
src/
├── adapters/mobility_ai_engine/
│   ├── __init__.py              # Module exports
│   ├── client.py                # HTTP async client
│   └── mapper.py                # Data normalization
│
├── orchestration/mobility/
│   ├── __init__.py              # Module exports
│   └── fleet_intelligence.py    # Business workflows
│
├── api/v1/
│   ├── routes/mobility_routes.py         # REST endpoints
│   └── schemas/mobility_schema.py        # Pydantic models
│
└── (autres branches)

docs/
├── MOBILITY_INTEGRATION.md      # Architecture détaillée
└── api-contracts.md             # API contracts

tests/
└── integration/test_mobility_routes.py   # Tests (14/14 ✓)
```

## 🚀 Démarrage Rapide

### 1. Installation

```bash
cd beryl-core-api
python3 -m venv venv
source venv/bin/activate
pip install -r pyproject.toml
```

### 2. Configuration

Créez un fichier `.env`:

```bash
cp .env.example.mobility .env
# Éditez .env avec votre configuration beryl-ai-engine
```

### 3. Démarrage

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

L'API sera disponible à: `http://localhost:8000`

Swagger UI: `http://localhost:8000/docs`

### 4. Tests

```bash
python3 -m pytest tests/integration/test_mobility_routes.py -v
```

## 📚 Endpoints API

### Prédiction de demande

```bash
curl -X POST http://localhost:8000/api/v1/mobility/demand/predict \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Paris-Center",
    "time_window": "hourly",
    "forecast_horizon": 24
  }'
```

### Optimisation de route

```bash
curl -X POST http://localhost:8000/api/v1/mobility/routing/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Paris-Gare-du-Nord",
    "destination": "Paris-LaDefense",
    "vehicle_type": "ebike",
    "battery_level": 85
  }'
```

### Analyse de flotte

```bash
curl -X POST http://localhost:8000/api/v1/mobility/fleet/fleet_paris_001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "fleet_id": "fleet_paris_001",
    "metrics": ["utilization", "battery_health"]
  }'
```

### État d'un véhicule

```bash
curl -X GET http://localhost:8000/api/v1/mobility/vehicle/vehicle_123/status
```

### Prédiction maintenance

```bash
curl -X GET http://localhost:8000/api/v1/mobility/vehicle/vehicle_123/maintenance
```

### Optimisation distribution

```bash
curl -X POST http://localhost:8000/api/v1/mobility/fleet/fleet_paris_001/optimize-distribution \
  -H "Content-Type: application/json" \
  -d '{
    "fleet_id": "fleet_paris_001",
    "target_locations": ["Paris-Center", "LaDefense", "Versailles"]
  }'
```

## 🔧 Configuration Avancée

### Client HTTP

**Timeout (par défaut 30s)**:
```python
client = MobilityAIClient(timeout=60)
```

**Retries (par défaut 3)**:
```python
client = MobilityAIClient(max_retries=5)
```

### Logging

**Niveaux**:
- `DEBUG`: Tous les appels API
- `INFO`: Événements métier importants
- `WARNING`: Alertes maintenance
- `ERROR`: Erreurs d'intégration

Configuration via `.env`:
```env
LOG_LEVEL=INFO
```

## 📊 Exemples de Réponses

### Demand Response

```json
{
  "location": "Paris-Center",
  "predicted_demand": 150.5,
  "confidence": 0.92,
  "time_window": "hourly",
  "forecast_horizon": 24,
  "forecast_data": [
    {"hour": 0, "demand": 45.2},
    {"hour": 1, "demand": 42.1}
  ],
  "timestamp": "2026-01-03T18:01:27.761Z"
}
```

### Route Response

```json
{
  "route_id": "route_abc123",
  "origin": "Paris-Gare-du-Nord",
  "destination": "Paris-LaDefense",
  "vehicle_type": "ebike",
  "distance_km": 12.5,
  "estimated_time_minutes": 28,
  "energy_consumption_kwh": 0.45,
  "waypoints": [...],
  "efficiency_score": 0.87,
  "timestamp": "2026-01-03T18:01:27.761Z"
}
```

### Fleet Analysis Response

```json
{
  "fleet_id": "fleet_paris_001",
  "total_vehicles": 250,
  "active_vehicles": 198,
  "utilization_rate": 79.2,
  "avg_battery_health": 89.5,
  "maintenance_alerts": [...],
  "key_insights": ["Peak demand 16:00-19:00"],
  "recommendations": ["Reposition 20 vehicles"],
  "timestamp": "2026-01-03T18:01:27.761Z"
}
```

## 🧪 Tests

### Tests disponibles

```bash
# Tous les tests
pytest tests/integration/test_mobility_routes.py -v

# Test spécifique
pytest tests/integration/test_mobility_routes.py::TestMobilityRoutes::test_routes_are_registered -v

# Avec coverage
pytest tests/integration/test_mobility_routes.py --cov=src.adapters.mobility_ai_engine --cov=src.orchestration.mobility
```

### Résultats attendus

```
14 passed in 1.11s
✅ Validation de schémas
✅ Normalisation de réponses
✅ Vérification des routes
✅ Intégration client/mapper/workflow
```

## 🔄 Intégration avec d'autres branches

### Fintech (beryl_mamba_core)
Les transactions de mobilité peuvent être orchestrées via les routes Fintech.

### ESG (berylcommunity-wb)
Les données de mobilité contribuent aux métriques de durabilité.

### Social (berylcommunity-ai-engine)
Les patterns de mobilité informent les recommandations sociales.

## 🚨 Gestion d'erreurs

### Erreurs courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| `500 Internal Server Error` | beryl-ai-engine inaccessible | Vérifiez MOBILITY_API_URL |
| `422 Unprocessable Entity` | Schéma invalide | Consultez la documentation |
| `timeout` | Réponse trop lente | Augmentez timeout (>30s) |

### Logs d'erreur

Consultez les logs pour debug:

```bash
grep "ERROR" application.log
grep "WARN" application.log
```

## 📈 Monitoring

### Métriques à surveiller

- **Latence API**: Cible < 500ms
- **Disponibilité**: Cible 99.9%
- **Erreurs**: Cible < 0.1%
- **Cache hit ratio**: Cible > 70% (avec Redis)

### Alertes recommandées

- API réponse > 1s
- Taux d'erreur > 1%
- Maintenance alerts > 5 véhicules

## 🔐 Sécurité

### Actuellement

- ✅ Validation Pydantic de toutes les entrées
- ✅ Sanitization des paramètres
- ✅ Logging sécurisé (pas de données sensibles)

### À venir

- [ ] Authentication JWT
- [ ] Rate limiting par client
- [ ] IP whitelisting
- [ ] Encryption des données sensibles

## 📝 Développement Futur

### Court terme (2-4 semaines)
- [ ] Redis caching pour prédictions
- [ ] Monitoring Prometheus
- [ ] Load testing

### Moyen terme (1-2 mois)
- [ ] WebSocket pour notifications temps réel
- [ ] Circuit breaker pour résilience
- [ ] Batch operations API

### Long terme (3+ mois)
- [ ] Real-time dashboard
- [ ] Advanced analytics
- [ ] ML pipeline integration
- [ ] Multi-region deployment

## 🤝 Support

Pour toute question:
- **Architecture**: Architecture team
- **Implémentation**: Backend team
- **ML/IA**: Data Science team

## 📄 Documentation Complète

- `docs/MOBILITY_INTEGRATION.md` - Architecture détaillée
- `docs/api-contracts.md` - API contracts officiels
- `MOBILITY_CHECKLIST.md` - Checklist de complétude
- `.env.example.mobility` - Configuration example

---

**Dernière mise à jour**: 2026-01-03T18:01:27.761Z  
**Version**: 1.0.0  
**Statut**: 🟢 Production-Ready
