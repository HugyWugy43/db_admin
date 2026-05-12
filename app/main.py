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

@app.on_event("startup")
async def ensure_admin_user():
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