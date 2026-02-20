# 🚀 Commandes Utiles - Mobilité

## 🔧 Setup Initial

```bash
# Clone et setup
cd beryl-core-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📝 Configuration

```bash
# Copier configuration example
cp .env.example.mobility .env

# Éditez avec vos paramètres beryl-ai-engine
nano .env
```

## 🚀 Démarrage

```bash
# Démarrage local (avec reload)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Démarrage production
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 🧪 Tests

```bash
# Tous les tests mobilité
pytest tests/integration/test_mobility_routes.py -v

# Test spécifique
pytest tests/integration/test_mobility_routes.py::TestMobilityRoutes -v

# Avec coverage
pytest tests/integration/test_mobility_routes.py --cov
```

## 📊 API Tests (cURL)

```bash
# Prédiction de demande
curl -X POST http://localhost:8000/api/v1/mobility/demand/predict \
  -H "Content-Type: application/json" \
  -d '{"location": "Paris", "time_window": "hourly", "forecast_horizon": 24}'

# Optimisation de route
curl -X POST http://localhost:8000/api/v1/mobility/routing/optimize \
  -H "Content-Type: application/json" \
  -d '{"origin": "A", "destination": "B", "vehicle_type": "ebike"}'

# Analyse de flotte
curl -X POST http://localhost:8000/api/v1/mobility/fleet/fleet_001/analyze \
  -H "Content-Type: application/json" \
  -d '{"fleet_id": "fleet_001"}'

# État d'un véhicule
curl -X GET http://localhost:8000/api/v1/mobility/vehicle/vehicle_001/status
```

## 📈 Validation & Linting

```bash
# Syntax check
python3 -m py_compile src/adapters/mobility_ai_engine/*.py

# Import check
python3 -c "from src.adapters.mobility_ai_engine import *; print('✅ OK')"

# Code formatting
black src/adapters/mobility_ai_engine/
isort src/adapters/mobility_ai_engine/
```

## 📝 Documentation

```bash
# Swagger UI
open http://localhost:8000/docs

# View docs
cat MOBILITY_README.md
cat docs/MOBILITY_INTEGRATION.md
```

## 🐳 Docker

```bash
# Build image
docker build -t beryl-core-api:latest .

# Run container
docker run -it --rm -p 8000:8000 beryl-core-api:latest

# Docker Compose
docker-compose up
docker-compose down
```

---

Cf. documentation complète: `MOBILITY_README.md`, `docs/MOBILITY_INTEGRATION.md`
