import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter

from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.application.services import UserService
from app.presentation.graphql.schemas import schema
from app.presentation.api.routers import auth, users, admin

app = FastAPI(title="DB Administrator", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статический фронтенд
app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

logger = logging.getLogger(__name__)


def _run_alembic_upgrade() -> None:
    """Миграции Alembic. Если таблицы уже есть из create_all, но нет alembic_version — stamp начальной ревизии."""
    from sqlalchemy import create_engine, text

    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    root = Path(__file__).resolve().parent.parent
    ini_path = str(root / "alembic.ini")

    eng = create_engine(sync_url)
    try:
        with eng.connect() as conn:
            n_users = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'users'"
                )
            ).scalar() or 0
            n_av = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'alembic_version'"
                )
            ).scalar() or 0
    finally:
        eng.dispose()

    cfg = Config(ini_path)
    if n_users > 0 and n_av == 0:
        command.stamp(cfg, "3bce1926ff36")

    try:
        command.upgrade(cfg, "head")
    except Exception as e:
        raise RuntimeError(f"alembic upgrade head failed: {e}") from e


@app.on_event("startup")
async def ensure_admin_user():
    await asyncio.to_thread(_run_alembic_upgrade)
    await init_db()
    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        existing_admin = await user_service.repo.get_by_username(settings.ADMIN_USERNAME)
        if existing_admin is None:
            await user_service.create_user(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                full_name=settings.ADMIN_FULL_NAME,
                role="admin"
            )

@app.get("/")
async def root():
    return {"message": "DB Administrator API запущен. Перейдите на /static/index.html"}