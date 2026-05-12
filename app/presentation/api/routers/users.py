"""
REST API роутер для управления пользователями
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.application.services import UserService

router = APIRouter()


@router.get("/")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Получение списка пользователей"""
    user_service = UserService(db)
    users = await user_service.get_all_users(skip, limit)
    return [u.model_dump(exclude={"password_hash"}) for u in users]


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Получение пользователя по ID"""
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user.model_dump(exclude={"password_hash"})


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Обновление пользователя"""
    user_service = UserService(db)
    user = await user_service.update_user(
        user_id,
        full_name=full_name,
        email=email,
    )
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user.model_dump(exclude={"password_hash"})


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удаление пользователя"""
    user_service = UserService(db)
    if not await user_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"message": "Пользователь удален"}
