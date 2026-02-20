import os
import psycopg2

def get_conn():
    return psycopg2.connect(
        os.getenv(
            "DATABASE_URL",
            "postgresql://neondb_owner@ep-dawn-glade-agvaoz3d-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require"
        )
    )
