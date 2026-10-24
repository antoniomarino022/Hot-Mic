"""Checkpointer management for LangGraph workflows (Postgres -> SQLite -> in-memory)."""

import logging
import os
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Optional, cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from config.settings import settings

logger = logging.getLogger("hotmic.agents.memory")

CHECKPOINT_BACKEND_ENV = "HOTMIC_CHECKPOINT_BACKEND"
DEFAULT_BACKEND = "sqlite"
POSTGRES_CONNECT_TIMEOUT_SECONDS = 3
SQLITE_DIR = Path("data")
SQLITE_FILENAME = "checkpoints.sqlite3"

_active_memory_checkpointer: BaseCheckpointSaver = MemorySaver()


# ---------------------------------------------------------------------------
# In-memory checkpointer
# ---------------------------------------------------------------------------


def get_checkpointer() -> BaseCheckpointSaver:
    """Return the in-memory checkpointer used for compiled StateGraph workflows."""
    return _active_memory_checkpointer


def reset_checkpointer_for_testing(
    custom_saver: Optional[BaseCheckpointSaver] = None,
) -> None:
    """Reset the in-memory checkpointer for clean, isolated test runs."""
    global _active_memory_checkpointer
    _active_memory_checkpointer = custom_saver or MemorySaver()


# ---------------------------------------------------------------------------
# Persistent backends
# ---------------------------------------------------------------------------


async def _open_postgres(stack: AsyncExitStack) -> BaseCheckpointSaver:
    """Open and set up a PostgreSQL saver; its lifetime is bound to `stack`."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    raw_url = settings.DATABASE_URL.get_secret_value()
    separator = "&" if "?" in raw_url else "?"
    conn_string = f"{raw_url}{separator}connect_timeout={POSTGRES_CONNECT_TIMEOUT_SECONDS}"

    saver = await stack.enter_async_context(AsyncPostgresSaver.from_conn_string(conn_string))
    await saver.setup()
    logger.info("Engaged production PostgreSQL async checkpointer.")
    return saver


async def _open_sqlite(stack: AsyncExitStack) -> BaseCheckpointSaver:
    """Open and set up a SQLite saver; its lifetime is bound to `stack`."""
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    db_path = SQLITE_DIR / SQLITE_FILENAME

    saver = await stack.enter_async_context(AsyncSqliteSaver.from_conn_string(str(db_path)))
    await saver.setup()
    logger.info("Engaged persistent SQLite async checkpointer at %s", db_path)
    return saver


async def _open_persistent_saver(
    stack: AsyncExitStack,
    backend: str,
) -> Optional[BaseCheckpointSaver]:
    """Try Postgres, then SQLite, depending on `backend`. Return None if all fail."""
    if settings.DATABASE_URL.get_secret_value():
        try:
            return await _open_postgres(stack)
        except Exception as exc:
            logger.warning(
                "PostgreSQL async checkpointer failed: %s. Falling back to persistent SQLite.",
                exc,
            )

    if backend in {"auto", "sqlite", "postgres"}:
        try:
            return await _open_sqlite(stack)
        except Exception as exc:
            logger.warning(
                "SQLite async checkpointer failed: %s. Falling back to in-memory checkpointer.",
                exc,
            )

    return None


@asynccontextmanager
async def get_async_checkpointer() -> AsyncGenerator[BaseCheckpointSaver, None]:
    """Yield a persistent async checkpointer, falling back to in-memory if needed."""
    async with AsyncExitStack() as stack:
        saver = await _open_persistent_saver(stack, DEFAULT_BACKEND)
        # `yield` stays outside any try/except so errors raised by the caller's
        # block are never mistaken for backend failures.
        yield saver or _active_memory_checkpointer


# ---------------------------------------------------------------------------
# Thread config & history
# ---------------------------------------------------------------------------


def get_thread_config(confession_id: int | str) -> RunnableConfig:
    """Build the LangGraph thread configuration for a confession."""
    return {"configurable": {"thread_id": f"confession_{confession_id}"}}


async def _read_channel_values(
    saver: BaseCheckpointSaver,
    config: RunnableConfig | dict[str, Any],
) -> Optional[dict[str, Any]]:
    checkpoint_tuple = await saver.aget_tuple(cast(RunnableConfig, config))
    if checkpoint_tuple and checkpoint_tuple.checkpoint:
        return checkpoint_tuple.checkpoint.get("channel_values")
    return None


async def get_confession_history(
    confession_id: int | str,
    checkpointer: Optional[BaseCheckpointSaver] = None,
) -> Optional[dict[str, Any]]:
    """Return persisted state values for a confession, or None if none exist."""
    config = get_thread_config(confession_id)

    if checkpointer is not None:
        return await _read_channel_values(checkpointer, config)

    async with get_async_checkpointer() as saver:
        return await _read_channel_values(saver, config)


__all__ = [
    "get_checkpointer",
    "get_async_checkpointer",
    "get_thread_config",
    "get_confession_history",
    "reset_checkpointer_for_testing",
]
