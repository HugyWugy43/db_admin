from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.application.services import UserService
from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


@router.post("/register", response_model=dict)
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    """Регистрация пользователя"""
    user_service = UserService(db)
    try:
        created_user = await user_service.create_user(
            username=user.username,
            email=user.email,
            password=user.password,
            full_name=user.full_name
        )
        return {
            "id": created_user.id,
            "username": created_user.username,
            "email": created_user.email,
            "full_name": created_user.full_name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    """Вход пользователя"""
    user_service = UserService(db)
    authenticated_user = await user_service.authenticate_user(user.username, user.password)
    
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    
    return {
        "access_token": f"token_{authenticated_user.id}",
        "token_type": "bearer",
        "user_id": authenticated_user.id,
        "username": authenticated_user.username
    }


@router.get("/me")
async def get_current_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получение текущего пользователя"""
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    data = user.model_dump(exclude={"password_hash"})
    return data