import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

APP_NAME = "Beryl Core API"
APP_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENV", "development")

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url=None,
)

# ======================
# Middleware
# ======================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, restreindre aux domaines Android / Web
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# Health & Root
# ======================

@app.get("/", tags=["system"])
async def root():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "status": "running"
    }

@app.get("/health", tags=["system"])
async def health():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": APP_NAME
        }
    )

# ======================
# Railway Entrypoint
# ======================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
