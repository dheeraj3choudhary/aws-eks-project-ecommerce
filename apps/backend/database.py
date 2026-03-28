"""
database.py
-----------
Handles SQLAlchemy engine + session setup.

Secrets are fetched from AWS Secrets Manager at startup using the IAM role
granted via IRSA (IAM Roles for Service Accounts).  The pod never needs a
long-lived access key — the OIDC token is exchanged automatically by the
AWS SDK.

Environment variables expected (set via K8s Deployment → env / valueFrom):
  DB_SECRET_NAME  – Name of the Secrets Manager secret  (e.g. "prod/ecommerce/db")
  AWS_REGION      – AWS region                           (e.g. "us-west-2")

The secret JSON must contain:
  {
    "username": "...",
    "password": "...",
    "host":     "...",
    "port":     "5432",
    "dbname":   "..."
  }

For local development without AWS, set the following env var instead and the
Secrets Manager lookup is skipped entirely:
  DATABASE_URL=postgresql://user:pass@localhost:5432/ecommerce
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_secret(secret_name: str, region: str) -> dict:
    """Fetch and parse a JSON secret from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=region)
    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        logger.error("Failed to retrieve secret '%s': %s", secret_name, error_code)
        raise RuntimeError(f"Secrets Manager error ({error_code})") from exc

    raw = response.get("SecretString") or response.get("SecretBinary", b"").decode()
    return json.loads(raw)


def _build_database_url() -> str:
    """
    Return a SQLAlchemy-compatible PostgreSQL URL.

    Priority:
    1. DATABASE_URL env var  (local dev / CI)
    2. Secrets Manager       (production on EKS)
    """
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        logger.info("Using DATABASE_URL from environment variable.")
        return direct_url

    secret_name = os.environ["DB_SECRET_NAME"]
    region      = os.getenv("AWS_REGION", "us-west-2")
    logger.info("Fetching DB credentials from Secrets Manager: %s", secret_name)

    secret = _get_secret(secret_name, region)
    username = secret["username"]
    password = secret["password"]
    host     = secret["host"]
    port     = secret.get("port", "5432")
    dbname   = secret["dbname"]

    return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"


# ── Engine & Session ──────────────────────────────────────────────────────────

DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # detect stale connections before use
    pool_size=5,              # keep 5 persistent connections
    max_overflow=10,          # allow 10 extra connections under load
    pool_recycle=1800,        # recycle connections every 30 min (RDS proxy friendly)
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base class for all ORM models ─────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_db():
    """
    Yield a database session and ensure it is closed after each request.
    Use as a FastAPI dependency:

        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Startup helper ────────────────────────────────────────────────────────────

def check_db_connection() -> bool:
    """Ping the database. Returns True on success, False on failure."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection OK.")
        return True
    except Exception as exc:
        logger.error("Database connection failed: %s", exc)
        return False