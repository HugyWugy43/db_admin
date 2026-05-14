"""
REST API роутер для администратора и управления БД
"""
from datetime import datetime
import os
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.application.services import DatabaseService, AdminService, QueryLogService
from app.domain.entities import Database

router = APIRouter()


def _backup_dir() -> str:
    """Каталог дампов (совпадает с DatabaseService.backup_database_to_file)."""
    return os.environ.get("BACKUP_DIR") or "/tmp/app_backups"


def _parse_form_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def _parse_bearer_user_id(authorization: Optional[str]) -> Optional[int]:
    """Токен вида Bearer token_<id> (как выдаёт /api/auth/login)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization[7:].strip()
    if token.startswith("token_"):
        try:
            return int(token.removeprefix("token_"))
        except ValueError:
            return None
    return None


class DatabasePublic(BaseModel):
    """Подключение к БД без пароля (ответ API)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    host: str
    port: int
    username: str
    database_name: str
    status: str
    owner_id: int
    access_privileges: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_checked: Optional[datetime] = None

    @classmethod
    def from_entity(cls, d: Database) -> "DatabasePublic":
        return cls(
            id=d.id,
            name=d.name,
            host=d.host,
            port=d.port,
            username=d.username,
            database_name=d.database_name,
            status=d.status,
            owner_id=d.owner_id,
            access_privileges=d.access_privileges,
            created_at=d.created_at,
            updated_at=d.updated_at,
            last_checked=d.last_checked,
        )


def _to_public_list(databases: List[Database]) -> List[DatabasePublic]:
    return [DatabasePublic.from_entity(x) for x in databases]


async def _require_owner_database(
    db_service: DatabaseService, database_id: int, user_id: int
) -> Database:
    d = await db_service.get_database(database_id)
    if d is None or d.owner_id != user_id:
        raise HTTPException(status_code=404, detail="БД не найдена")
    return d


@router.post("/databases", response_model=DatabasePublic)
async def create_database(
    host: str = Form(...),
    port: int = Form(5432),
    username: str = Form(...),
    password: str = Form(...),
    database_name: str = Form(...),
    create_on_server: str = Form("false"),
    maintenance_database: str = Form("postgres"),
    access_privileges: str = Form(""),
    apply_privileges: str = Form("false"),
    owner_id: Optional[int] = Form(None),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """
    Регистрация подключения к PostgreSQL.
    При create_on_server=true выполняется CREATE DATABASE на сервере.
    access_privileges — JSON-массив строк (CONNECT, SELECT, …); при apply_privileges=true
    выдаются права роли username на созданную/указанную БД (нужны права администратора).
    """
    token_uid = _parse_bearer_user_id(authorization)
    effective_owner = token_uid if token_uid is not None else owner_id
    if effective_owner is None:
        raise HTTPException(
            status_code=400,
            detail="Укажите owner_id в форме или войдите (Bearer token_<id>)",
        )

    final_db = (database_name or "").strip()
    if not final_db:
        raise HTTPException(status_code=400, detail="Укажите имя базы данных")

    res_host = (host or "").strip()
    if not res_host:
        raise HTTPException(status_code=400, detail="Укажите хост")

    res_port = port
    db_service = DatabaseService(db)
    priv_list = db_service.normalize_privileges_json(access_privileges)
    priv_json_str = db_service.privileges_json_string(priv_list)

    if _parse_form_bool(create_on_server):
        maint = (maintenance_database or "").strip() or "postgres"
        try:
            final_db = await db_service.create_postgresql_database_if_missing(
                host=res_host,
                port=port,
                username=username,
                password=password,
                new_database=final_db,
                maintenance_database=maint,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    else:
        maint = (maintenance_database or "").strip() or "postgres"

    display_name = final_db

    try:
        database = await db_service.create_database(
            name=display_name,
            host=res_host,
            port=port,
            username=username,
            password=password,
            database_name=final_db,
            owner_id=effective_owner,
            access_privileges=priv_json_str,
        )
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="У вас уже есть подключение с таким именем базы на этом сервере (тот же хост и порт). "
            "На другом сервере то же имя допустимо.",
        ) from e

    if _parse_form_bool(apply_privileges):
        try:
            await db_service.apply_database_role_privileges(
                host=res_host,
                port=port,
                admin_user=username,
                admin_password=password,
                database_name=final_db,
                grantee_role=username,
                privileges=priv_list,
                maintenance_database=maint,
            )
        except RuntimeError as e:
            await db_service.delete_database(database.id)
            raise HTTPException(status_code=400, detail=str(e)) from e

    log_uid = token_uid if token_uid is not None else effective_owner
    if log_uid is not None and database.id is not None:
        try:
            await QueryLogService(db).log_query(
                log_uid,
                database.id,
                f'База «{display_name}» → {res_host}:{res_port}/{final_db}',
                "success",
                None,
                0.0,
            )
        except Exception:
            pass
    return DatabasePublic.from_entity(database)


@router.get("/databases", response_model=List[DatabasePublic])
async def get_databases(
    owner_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Список сохранённых подключений к БД текущего пользователя (владелец)."""
    db_service = DatabaseService(db)
    token_uid = _parse_bearer_user_id(authorization)
    effective_owner = token_uid if token_uid is not None else owner_id
    if effective_owner is None:
        raise HTTPException(
            status_code=400,
            detail="Укажите owner_id или войдите (Authorization: Bearer token_<id>)",
        )
    databases = await db_service.get_user_databases(effective_owner, skip, limit)
    return _to_public_list(databases)


@router.get("/databases/{database_id}", response_model=DatabasePublic)
async def get_database(
    database_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Получение БД по ID (без пароля в ответе)."""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await _require_owner_database(db_service, database_id, uid)
    return DatabasePublic.from_entity(database)


@router.post("/databases/{database_id}/test-connection")
async def test_database_connection(
    database_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Тестирование подключения к БД"""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await _require_owner_database(db_service, database_id, uid)

    is_connected = await db_service.test_connection(
        database.host,
        database.port,
        database.username,
        database.password,
        database.database_name,
    )

    if is_connected:
        await db_service.update_database_status(database_id, "connected")
        return {"status": "connected"}
    else:
        await db_service.update_database_status(database_id, "error")
        return {"status": "error", "message": "Не удалось подключиться"}


@router.get("/databases/{database_id}/tables")
async def get_database_tables(
    database_id: int,
    schema: str = "public",
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Получение таблиц БД"""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await _require_owner_database(db_service, database_id, uid)

    try:
        tables = await db_service.get_database_tables(
            database.host,
            database.port,
            database.username,
            database.password,
            database.database_name,
            schema,
        )
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{database_id}/schemas")
async def get_database_schemas(
    database_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Получение схем БД"""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await _require_owner_database(db_service, database_id, uid)

    try:
        schemas = await db_service.get_database_schemas(
            database.host,
            database.port,
            database.username,
            database.password,
            database.database_name,
        )
        return schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{database_id}/server-databases")
async def get_server_catalog_databases(
    database_id: int,
    maintenance_database: str = Query("postgres"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Список имён баз в кластере (подключение к служебной БД, по умолчанию postgres)."""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await _require_owner_database(db_service, database_id, uid)
    try:
        return await db_service.list_server_catalog_databases(
            database.host,
            database.port,
            database.username,
            database.password,
            maintenance_database=maintenance_database or "postgres",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/databases/{database_id}/tables/{table_name}/columns")
async def get_table_columns(
    database_id: int,
    table_name: str,
    schema: str = "public",
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Получение схемы таблицы"""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await _require_owner_database(db_service, database_id, uid)

    try:
        columns = await db_service.get_table_columns(
            database.host,
            database.port,
            database.username,
            database.password,
            database.database_name,
            schema,
            table_name,
        )
        return columns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{database_id}/tables/{table_name}/rows")
async def get_table_rows(
    database_id: int,
    table_name: str,
    schema: str = "public",
    limit: int = 50,
    offset: int = 0,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Получение данных таблицы"""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await _require_owner_database(db_service, database_id, uid)

    try:
        rows = await db_service.get_table_rows(
            database.host,
            database.port,
            database.username,
            database.password,
            database.database_name,
            schema,
            table_name,
            limit,
            offset,
        )
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/databases/{database_id}")
async def delete_database(
    database_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Удаление записи о подключении (только владелец)."""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await db_service.get_database(database_id)
    if database is None or database.owner_id != uid:
        raise HTTPException(status_code=404, detail="БД не найдена")
    if not await db_service.delete_database(database_id):
        raise HTTPException(status_code=404, detail="БД не найдена")
    return {"message": "БД удалена"}


@router.post("/databases/{database_id}/backup")
async def backup_database(
    database_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Резервная копия через pg_dump (по умолчанию каталог внутри контейнера, см. BACKUP_DIR)."""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    db_service = DatabaseService(db)
    database = await db_service.get_database(database_id)
    if not database or database.owner_id != uid:
        raise HTTPException(status_code=404, detail="БД не найдена")
    try:
        fname, size = await db_service.backup_database_to_file(database)
    except RuntimeError as e:
        try:
            await QueryLogService(db).log_query(
                uid,
                database_id,
                "BACKUP pg_dump",
                "error",
                str(e)[:1000],
                0.0,
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка бэкапа: {e!s}") from e
    try:
        await QueryLogService(db).log_query(
            uid,
            database_id,
            f"BACKUP pg_dump → {fname} ({size} bytes)",
            "success",
            None,
            0.0,
        )
    except Exception:
        pass
    return {
        "filename": fname,
        "size_bytes": size,
        "message": f"Копия сохранена в {_backup_dir()} (внутри контейнера приложения). "
        "Для каталога на хосте задайте BACKUP_DIR в .env, например /app/backups при монтировании тома.",
    }


@router.get("/databases/{database_id}/backups/download")
async def download_backup(
    database_id: int,
    filename: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """Скачивание ранее созданного дампа (только своё подключение)."""
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    if not re.match(rf"^db_{database_id}_\d{{8}}_\d{{6}}\.sql$", filename):
        raise HTTPException(status_code=400, detail="Некорректное имя файла")
    db_service = DatabaseService(db)
    database = await db_service.get_database(database_id)
    if not database or database.owner_id != uid:
        raise HTTPException(status_code=404, detail="БД не найдена")
    path = os.path.join(_backup_dir(), filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path, filename=filename, media_type="application/sql")


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
):
    """Получение статистики системы"""
    admin_service = AdminService(db)
    stats = await admin_service.get_system_statistics()
    return stats


@router.get("/dashboard")
async def get_dashboard(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """
    Расширенный дашборд: сводка + метрики по каждому подключению (размер БД в PostgreSQL, сессии).
    Свободное место на диске сервера через SQL стандартно не показывается.
    """
    uid = _parse_bearer_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    admin_service = AdminService(db)
    return await admin_service.get_user_dashboard(uid)


@router.get("/logs")
async def get_query_logs(
    database_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Логи запросов: по database_id или все."""
    log_service = QueryLogService(db)
    if database_id is not None:
        logs = await log_service.get_database_logs(database_id, skip, limit)
    else:
        logs = await log_service.get_all_logs(skip, limit)
    return logs
