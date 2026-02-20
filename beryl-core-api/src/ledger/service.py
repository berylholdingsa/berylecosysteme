from typing import Optional

from src.db.pg import get_conn


def get_or_create_account(user_id: str, currency: str) -> str:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM accounts WHERE user_id = %s AND currency = %s",
                (user_id, currency),
            )
            row = cur.fetchone()
            if row:
                return str(row[0])

            cur.execute(
                """
                INSERT INTO accounts (user_id, currency)
                VALUES (%s, %s)
                RETURNING id
                """,
                (user_id, currency),
            )
            account_id = cur.fetchone()[0]
            conn.commit()
            return str(account_id)
    finally:
        conn.close()


def post_entry(account_id: str, amount: float, direction: str, ref: Optional[str]) -> str:
    normalized = direction.upper()
    if normalized not in {"DEBIT", "CREDIT"}:
        raise ValueError("direction must be DEBIT or CREDIT")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ledger_entries (account_id, amount, direction, reference)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (account_id, amount, normalized, ref),
            )
            entry_id = cur.fetchone()[0]
            conn.commit()
            return str(entry_id)
    finally:
        conn.close()
