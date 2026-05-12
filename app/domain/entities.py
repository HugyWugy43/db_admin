"""
Доменные сущности приложения - бизнес-объекты независимо от деталей реализации
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """Роли пользователей"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class DatabaseStatus(str, Enum):
    """Статус подключения к БД"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class User(BaseModel):
    """Сущность пользователя"""
    id: Optional[int] = None
    username: str
    email: str
    full_name: Optional[str] = None
    password_hash: Optional[str] = None
    role: str = "viewer"  # admin, user, viewer
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Project(BaseModel):
    """Сущность проекта"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Database(BaseModel):
    """Сущность подключения к БД"""
    id: Optional[int] = None
    name: str
    host: str
    port: int = 5432
    username: str
    password: str
    database_name: str
    status: str = "disconnected"
    owner_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Column(BaseModel):
    """Сущность колонки таблицы"""
    id: Optional[int] = None
    name: str
    table_id: Optional[int] = None
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_unique: bool = False
    default_value: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TableInfo(BaseModel):
    """Сущность таблицы БД"""
    id: Optional[int] = None
    name: str
    database_id: Optional[int] = None
    row_count: int = 0
    size_bytes: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    columns: List[Column] = Field(default_factory=list)
    
    class Config:
        from_attributes = True

class Index(BaseModel):
    """Сущность индекса БД"""
    id: Optional[int] = None
    name: str
    table_id: Optional[int] = None
    columns: List[str] = Field(default_factory=list)
    is_unique: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class QueryLog(BaseModel):
    """Логирование запросов"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    database_id: Optional[int] = None
    query_text: str
    status: str = "success"
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BackupLog(BaseModel):
    """Логирование резервных копий"""
    id: Optional[int] = None
    database_id: Optional[int] = None
    user_id: Optional[int] = None
    backup_name: str
    size_bytes: int = 0
    status: str = "pending"
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
