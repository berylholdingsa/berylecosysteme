from typing import Optional

def get_or_create_user_id(conn, firebase_uid: str, email: Optional[str], phone: Optional[str]) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM users WHERE firebase_uid = %s",
            (firebase_uid,),
        )
        row = cur.fetchone()
        if row:
            return str(row[0])

        cur.execute(
            """
            INSERT INTO users (firebase_uid, email, phone)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (firebase_uid, email, phone),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return str(user_id)
