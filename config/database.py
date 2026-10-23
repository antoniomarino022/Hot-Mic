from collections.abc import Generator
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import NullPool

from config.settings import settings

# Retrieve the raw connection string from the SecretStr
database_url = settings.DATABASE_URL.get_secret_value()

# Add connection timeout for PostgreSQL to prevent startup hanging when DB is offline
connect_args = {"connect_timeout": 3} if database_url.startswith("postgresql") else {}

# For serverless deployment (Vercel) + Neon connection pooler:
# NullPool disables client-side connection pooling, allowing Neon's PgBouncer
# to manage incoming connections effectively without leaking resources.
engine = create_engine(
    database_url,
    echo=False,
    poolclass=NullPool,
    connect_args=connect_args,
)


def init_db() -> None:
    """Create all database tables defined in SQLModel metadata."""
    import src.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    with Session(engine) as session:
        yield session
