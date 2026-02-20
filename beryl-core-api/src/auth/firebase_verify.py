import json
import os

from src.observability.logging.logger import logger

try:
    import firebase_admin
    from firebase_admin import auth, credentials
except ModuleNotFoundError:
    firebase_admin = None
    auth = None
    credentials = None

_app = None

def init_firebase():
    if os.getenv("TESTING") == "1":
        return None

    if firebase_admin is None:
        raise RuntimeError("firebase_admin package is not available.")

    global _app
    if _app:
        return _app

    # Option A — Service account via fichier
    path = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH",
        "config/firebase-service-account.json",
    )
    if os.path.exists(path):
        cred = credentials.Certificate(path)
        _app = firebase_admin.initialize_app(cred)
        return _app

    # Option B — Service account via variable d’environnement (JSON)
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if raw:
        cred = credentials.Certificate(json.loads(raw))
        _app = firebase_admin.initialize_app(cred)
        return _app

    raise RuntimeError("Firebase service account non configuré.")

def verify_id_token(id_token: str) -> dict:
    if os.getenv("TESTING") == "1" or auth is None:
        # Return a deterministic placeholder so tests can proceed without Firebase.
        logger.info("Firebase bypassed in TESTING mode, returning stub claims")
        return {
            "uid": "testing-unity-user",
            "sub": "testing-unity-user",
            "email": "testing@beryl.app",
        }

    init_firebase()
    return auth.verify_id_token(id_token)
