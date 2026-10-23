import anyio
import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.database import init_db
from config.settings import settings
from src.models import User
from src.routers import (
    auth_router,
    confession_router,
    get_optional_current_user,
)

logger = logging.getLogger("hotmic")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: initializes database tables on startup without blocking server boot."""
    async def run_db_init():
        try:
            await anyio.to_thread.run_sync(init_db)
            logger.info("Database tables initialized successfully.")
        except Exception as exc:
            logger.warning(
                "Could not initialize database on startup (expected if local/Neon DB is offline): %s",
                exc,
            )

    asyncio.create_task(run_db_init())
    yield


app = FastAPI(
    title="Hot-Mic",
    description="Anonymous confession platform with AI Roast Judge and Telegram Auth",
    version="0.1.0",
    lifespan=lifespan,
)

# Static files (Tailwind CSS, assets, etc.)
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Jinja2 template engine configuration
templates = Jinja2Templates(directory="src/templates")

# Include API routers
app.include_router(auth_router)
app.include_router(confession_router)


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Home page: redirect to registration if not authenticated, otherwise show confession page."""
    if not current_user:
        return RedirectResponse(url="/register", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="confession.html",
        context={
            "bot_username": settings.TELEGRAM_BOT_USERNAME,
            "user": current_user,
        },
    )


@app.get("/confession", response_class=HTMLResponse)
async def confession_page(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Confession creation page."""
    if not current_user:
        return RedirectResponse(url="/register", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="confession.html",
        context={
            "bot_username": settings.TELEGRAM_BOT_USERNAME,
            "user": current_user,
        },
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Registration and Telegram authentication page."""
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "bot_username": settings.TELEGRAM_BOT_USERNAME,
            "user": current_user,
        },
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "Hot-Mic"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
