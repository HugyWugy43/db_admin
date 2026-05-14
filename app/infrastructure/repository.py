"""
Инфраструктурный слой - репозитории для доступа к данным
"""
from typing import List, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import (
    UserModel,
    DatabaseModel,
    TableModel,
    ColumnModel,
    IndexModel,
    QueryLogModel,
    BackupLogModel,
)
from app.domain.entities import (
    User,
    Database,
    TableInfo,
    Column,
    Index,
    QueryLog,
    BackupLog,
)


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _row_to_user(row: UserModel) -> User:
        """ORM → домен: колонка hashed_password → поле password_hash."""
        return User(
            id=row.id,
            username=row.username,
            email=row.email,
            full_name=row.full_name,
            password_hash=row.hashed_password,
            role=row.role,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _user_to_row_kwargs(user: User) -> dict:
        """Домен → ORM для конструктора UserModel."""
        data = user.model_dump(exclude={"id", "password_hash"})
        if user.password_hash is not None:
            data["hashed_password"] = user.password_hash
        return data
    
    async def create(self, user: User) -> User:
        """Создание пользователя"""
        db_user = UserModel(**self._user_to_row_kwargs(user))
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return self._row_to_user(db_user)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalars().first()
        return self._row_to_user(user) if user else None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по имени"""
        result = await self.db.execute(select(UserModel).where(UserModel.username == username))
        user = result.scalars().first()
        return self._row_to_user(user) if user else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        result = await self.db.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalars().first()
        return self._row_to_user(user) if user else None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение всех пользователей"""
        result = await self.db.execute(
            select(UserModel).offset(skip).limit(limit)
        )
        users = result.scalars().all()
        return [self._row_to_user(u) for u in users]
    
    async def update(self, user_id: int, user: User) -> Optional[User]:
        """Обновление пользователя"""
        result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalars().first()
        if db_user:
            for field, value in user.model_dump(exclude={"id"}, exclude_unset=True).items():
                if field == "password_hash":
                    setattr(db_user, "hashed_password", value)
                else:
                    setattr(db_user, field, value)
            await self.db.commit()
            await self.db.refresh(db_user)
            return self._row_to_user(db_user)
        return None
    
    async def delete(self, user_id: int) -> bool:
        """Удаление пользователя"""
        result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
        db_user = result.scalars().first()
        if db_user:
            await self.db.delete(db_user)
            await self.db.commit()
            return True
        return False

    async def count_all(self) -> int:
        q = await self.db.execute(select(func.count()).select_from(UserModel))
        return int(q.scalar_one())


class DatabaseRepository:
    """Репозиторий для работы с подключениями БД"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, database: Database) -> Database:
        """Создание подключения к БД"""
        db_database = DatabaseModel(**database.model_dump(exclude={'id'}))
        self.db.add(db_database)
        await self.db.commit()
        await self.db.refresh(db_database)
        return Database.model_validate(db_database, from_attributes=True)
    
    async def get_by_id(self, db_id: int) -> Optional[Database]:
        """Получение БД по ID"""
        result = await self.db.execute(
            select(DatabaseModel).where(DatabaseModel.id == db_id)
        )
        db = result.scalars().first()
        return Database.model_validate(db, from_attributes=True) if db else None
    
    async def get_by_owner(self, owner_id: int, skip: int = 0, limit: int = 100) -> List[Database]:
        """Получение всех БД пользователя"""
        result = await self.db.execute(
            select(DatabaseModel).where(DatabaseModel.owner_id == owner_id).offset(skip).limit(limit)
        )
        databases = result.scalars().all()
        return [Database.model_validate(db, from_attributes=True) for db in databases]
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Database]:
        """Получение всех БД"""
        result = await self.db.execute(
            select(DatabaseModel).offset(skip).limit(limit)
        )
        databases = result.scalars().all()
        return [Database.model_validate(db, from_attributes=True) for db in databases]
    
    async def update(self, db_id: int, database: Database) -> Optional[Database]:
        """Обновление БД"""
        result = await self.db.execute(
            select(DatabaseModel).where(DatabaseModel.id == db_id)
        )
        db = result.scalars().first()
        if db:
            for field, value in database.model_dump(exclude={'id'}, exclude_unset=True).items():
                setattr(db, field, value)
            await self.db.commit()
            await self.db.refresh(db)
            return Database.model_validate(db, from_attributes=True)
        return None

    async def count_all(self) -> int:
        q = await self.db.execute(select(func.count()).select_from(DatabaseModel))
        return int(q.scalar_one())

    async def count_by_status(self, status: str) -> int:
        q = await self.db.execute(
            select(func.count())
            .select_from(DatabaseModel)
            .where(DatabaseModel.status == status)
        )
        return int(q.scalar_one())
    
    async def delete(self, db_id: int) -> bool:
        """Удаление подключения и связанных записей (логи, локальные метаданные таблиц)."""
        result = await self.db.execute(select(DatabaseModel).where(DatabaseModel.id == db_id))
        db = result.scalars().first()
        if not db:
            return False
        await self.db.execute(delete(QueryLogModel).where(QueryLogModel.database_id == db_id))
        await self.db.execute(delete(BackupLogModel).where(BackupLogModel.database_id == db_id))
        t_ids = (
            await self.db.execute(select(TableModel.id).where(TableModel.database_id == db_id))
        ).scalars().all()
        for tid in t_ids:
            await self.db.execute(delete(ColumnModel).where(ColumnModel.table_id == tid))
            await self.db.execute(delete(IndexModel).where(IndexModel.table_id == tid))
        await self.db.execute(delete(TableModel).where(TableModel.database_id == db_id))
        await self.db.delete(db)
        await self.db.commit()
        return True


class TableRepository:
    """Репозиторий для работы с таблицами БД"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, table: TableInfo) -> TableInfo:
        """Создание таблицы"""
        db_table = TableModel(**table.model_dump(exclude={'id', 'columns'}))
        self.db.add(db_table)
        await self.db.commit()
        await self.db.refresh(db_table)
        return TableInfo.from_orm(db_table)
    
    async def get_by_id(self, table_id: int) -> Optional[TableInfo]:
        """Получение таблицы по ID"""
        result = await self.db.execute(
            select(TableModel).where(TableModel.id == table_id)
        )
        table = result.scalars().first()
        return TableInfo.from_orm(table) if table else None
    
    async def get_by_database(self, database_id: int, skip: int = 0, limit: int = 100) -> List[TableInfo]:
        """Получение всех таблиц БД"""
        result = await self.db.execute(
            select(TableModel)
            .where(TableModel.database_id == database_id)
            .offset(skip).limit(limit)
        )
        tables = result.scalars().all()
        return [TableInfo.from_orm(t) for t in tables]
    
    async def update(self, table_id: int, table: TableInfo) -> Optional[TableInfo]:
        """Обновление таблицы"""
        result = await self.db.execute(
            select(TableModel).where(TableModel.id == table_id)
        )
        db_table = result.scalars().first()
        if db_table:
            for field, value in table.model_dump(exclude={'id', 'columns'}, exclude_unset=True).items():
                setattr(db_table, field, value)
            await self.db.commit()
            await self.db.refresh(db_table)
            return TableInfo.from_orm(db_table)
        return None
    
    async def delete(self, table_id: int) -> bool:
        """Удаление таблицы"""
        result = await self.db.execute(
            select(TableModel).where(TableModel.id == table_id)
        )
        table = result.scalars().first()
        if table:
            await self.db.delete(table)
            await self.db.commit()
            return True
        return False


class QueryLogRepository:
    """Репозиторий для логирования запросов"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, query_log: QueryLog) -> QueryLog:
        """Создание лога запроса"""
        db_log = QueryLogModel(**query_log.model_dump(exclude={'id'}))
        self.db.add(db_log)
        await self.db.commit()
        await self.db.refresh(db_log)
        return QueryLog.model_validate(db_log, from_attributes=True)
    
    async def get_by_database(self, database_id: int, skip: int = 0, limit: int = 100) -> List[QueryLog]:
        """Получение логов БД"""
        result = await self.db.execute(
            select(QueryLogModel)
            .where(QueryLogModel.database_id == database_id)
            .offset(skip).limit(limit)
            .order_by(QueryLogModel.created_at.desc())
        )
        logs = result.scalars().all()
        return [QueryLog.model_validate(l, from_attributes=True) for l in logs]

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[QueryLog]:
        """Все логи запросов (новые сверху)"""
        result = await self.db.execute(
            select(QueryLogModel)
            .offset(skip)
            .limit(limit)
            .order_by(QueryLogModel.created_at.desc())
        )
        logs = result.scalars().all()
        return [QueryLog.model_validate(l, from_attributes=True) for l in logs]
    
    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[QueryLog]:
        """Получение логов пользователя"""
        result = await self.db.execute(
            select(QueryLogModel)
            .where(QueryLogModel.user_id == user_id)
            .offset(skip).limit(limit)
            .order_by(QueryLogModel.created_at.desc())
        )
        logs = result.scalars().all()
        return [QueryLog.model_validate(l, from_attributes=True) for l in logs]
