"""
GraphQL схема и типы
"""
import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class UserType:
    """GraphQL тип пользователя"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@strawberry.type
class DatabaseType:
    """GraphQL тип БД"""
    id: int
    name: str
    host: str
    port: int
    database_name: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_checked: Optional[datetime] = None


@strawberry.type
class TableType:
    """GraphQL тип таблицы"""
    id: int
    name: str
    row_count: int
    size_bytes: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@strawberry.type
class ColumnType:
    """GraphQL тип колонки"""
    id: int
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_unique: bool
    default_value: Optional[str] = None


@strawberry.type
class IndexType:
    """GraphQL тип индекса"""
    id: int
    name: str
    columns: List[str]
    is_unique: bool


@strawberry.type
class QueryLogType:
    """GraphQL тип лога запроса"""
    id: int
    query_text: str
    status: str
    error_message: Optional[str] = None
    execution_time_ms: float
    created_at: Optional[datetime] = None


@strawberry.type
class StatisticsType:
    """GraphQL тип статистики"""
    total_users: int
    total_databases: int
    total_queries: int
    avg_query_time_ms: float


@strawberry.type
class Query:
    """GraphQL Query типы"""
    
    @strawberry.field
    async def hello(self, name: str = "World") -> str:
        """Проверка связи"""
        return f"Hello, {name}!"
    
    @strawberry.field
    async def get_user(self, user_id: int) -> Optional[UserType]:
        """Получение пользователя"""
        return None
    
    @strawberry.field
    async def list_users(self, skip: int = 0, limit: int = 10) -> List[UserType]:
        """Список пользователей"""
        return []
    
    @strawberry.field
    async def get_database(self, database_id: int) -> Optional[DatabaseType]:
        """Получение БД"""
        return None
    
    @strawberry.field
    async def list_databases(self, skip: int = 0, limit: int = 10) -> List[DatabaseType]:
        """Список БД"""
        return []
    
    @strawberry.field
    async def get_tables(self, database_id: int) -> List[TableType]:
        """Получение таблиц БД"""
        return []
    
    @strawberry.field
    async def get_query_logs(self, database_id: int, limit: int = 50) -> List[QueryLogType]:
        """Получение логов запросов"""
        return []


@strawberry.type
class Mutation:
    """GraphQL Mutation типы"""
    
    @strawberry.mutation
    async def create_user(self, username: str, email: str, password: str) -> UserType:
        """Создание пользователя"""
        return None
    
    @strawberry.mutation
    async def create_database(
        self, name: str, host: str, port: int, 
        username: str, password: str, database_name: str
    ) -> DatabaseType:
        """Создание подключения к БД"""
        return None
    
    @strawberry.mutation
    async def test_database_connection(
        self, host: str, port: int, username: str, 
        password: str, database_name: str
    ) -> bool:
        """Тестирование подключения к БД"""
        return False
    
    @strawberry.mutation
    async def delete_database(self, database_id: int) -> bool:
        """Удаление БД"""
        return False


schema = strawberry.Schema(query=Query, mutation=Mutation)