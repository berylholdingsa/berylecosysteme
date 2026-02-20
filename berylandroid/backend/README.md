# Beryl Backend (Ktor + Firebase + Firestore)

Production-ready backend that centralizes sensitive business logic and data access.

## Architecture
```
backend/
 ├── build.gradle.kts
 ├── settings.gradle.kts
 └── src/main/kotlin/
     ├── Application.kt
     ├── routes/
     ├── services/
     ├── repositories/
     ├── models/
     └── security/
```

## Configuration
Create a `.env` file in `backend/` or export environment variables:

Required:
- `FIREBASE_PROJECT_ID`
- `FIREBASE_SERVICE_ACCOUNT_JSON` **or** `FIREBASE_SERVICE_ACCOUNT_PATH`

Optional:
- `PORT` (default `8080`)
- `RATE_LIMIT_PER_MINUTE` (default `120`)
- `RATE_LIMIT_BURST` (default `30`)
- `CORS_ALLOWED_ORIGINS` (default `*`, otherwise comma-separated hostnames)
- `REDIS_URL` (recommended for production rate limiting)
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_TLS` (alternative to `REDIS_URL`)

Example: see `.env.example`.

## Local Run
From repository root:
```
./gradlew -p backend run
```

Or inside backend:
```
cd backend
gradle run
```

## Docker
Build:
```
docker build -t beryl-backend backend
```

Run:
```
docker run --rm -p 8080:8080 \
  -e FIREBASE_PROJECT_ID=your-project-id \
  -e FIREBASE_SERVICE_ACCOUNT_PATH=/secrets/firebase-service-account.json \
  -e REDIS_URL=redis://your-redis-host:6379 \
  -v /path/to/service-account.json:/secrets/firebase-service-account.json \
  beryl-backend
```

## Tests
Run integration tests:
```
./gradlew -p backend test
```

## API Docs
- OpenAPI spec: `GET /openapi`
- Swagger UI: `GET /docs`

## Endpoints
All protected endpoints require `Authorization: Bearer <Firebase ID Token>`.

- `POST /auth/verify`
  - Body: `{ "idToken": "..." }`
  - Verifies token and returns identity metadata.

- `GET /users/me`
  - Returns or creates the user profile in Firestore.

- `POST /business/compute`
  - Body: `{ "signal": "...", "weight": 1-100, "factors": [0-100] }`
  - Executes sensitive business logic on the server.

- `POST /community/post`
  - Body: `{ "content": "...", "tags": ["..."] }`
  - Creates a community post in Firestore.

- `GET /community/feed?limit=20`
  - Returns most recent community posts.

## Notes
- No API keys are hard-coded. Secrets come from environment variables or `.env`.
- Firestore collections used: `users`, `community_posts`.
