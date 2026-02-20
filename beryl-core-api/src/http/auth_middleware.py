from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from firebase_admin import auth

from src.db.pg import get_conn
from src.auth.firebase_verify import init_firebase


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        id_token = auth_header.split(" ", 1)[1].strip()
        if not id_token:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        try:
            init_firebase()
            decoded = auth.verify_id_token(id_token)
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        firebase_uid = decoded.get("uid") or decoded.get("sub")
        email = decoded.get("email")
        phone = decoded.get("phone_number") or decoded.get("phone")
        if not firebase_uid:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        user_id = _upsert_user(firebase_uid, email, phone)
        request.state.user_id = user_id

        return await call_next(request)


def _upsert_user(firebase_uid: str, email: Optional[str], phone: Optional[str]) -> str:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (firebase_uid, email, phone)
                VALUES (%s, %s, %s)
                ON CONFLICT (firebase_uid) DO UPDATE
                SET email = COALESCE(EXCLUDED.email, users.email),
                    phone = COALESCE(EXCLUDED.phone, users.phone),
                    updated_at = now()
                RETURNING id
                """,
                (firebase_uid, email, phone),
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return str(user_id)
    finally:
        conn.close()
