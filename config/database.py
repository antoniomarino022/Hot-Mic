from collections.abc import Generator
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import NullPool

from config.setting import setting

# Retrieve the raw connection string from the SecretStr
database_url = setting.DATABASE_URL.get_secret_value()

# For serverless deployment (Vercel) + Neon connection pooler:
# NullPool disables client-side connection pooling, allowing Neon's PgBouncer
# to manage incoming connections effectively without leaking resources.
engine = create_engine(
    database_url,
    echo=False,
    poolclass=NullPool,
)


def init_db() -> None:
    """Create all database tables defined in SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    with Session(engine) as session:
        yield session
