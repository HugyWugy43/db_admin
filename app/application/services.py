"""
Слой сервисов - бизнес-логика приложения
"""
import json
import asyncio
import logging
import os
import re
import shutil
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repository import (
    UserRepository,
    DatabaseRepository,
    TableRepository,
    QueryLogRepository,
)
from app.domain.entities import User, Database, TableInfo, QueryLog
import asyncpg

# Контекст для хеширования паролей
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _validate_identifier(identifier: str) -> str:
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', identifier):
        raise ValueError("Invalid identifier")
    return identifier


def _validate_pg_new_db_name(name: str) -> str:
    """
    Имя для CREATE DATABASE без кавычек: к нижнему регистру, латиница/цифры/_,
    не длиннее 63 символов (NAMEDATALEN в PostgreSQL).
    """
    s = (name or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", s):
        raise ValueError(
            "Имя базы для создания на сервере: строчные латинские буквы, цифры и подчёркивание, "
            "до 63 символов, первый символ — буква."
        )
    return s


def _asyncpg_ssl_kw() -> dict:
    """Совместимо с libpq/pg_dump: при PGSSLMODE=disable не пытаемся TLS (типичный dev Docker)."""
    if os.environ.get("PGSSLMODE", "disable").lower() == "disable":
        return {"ssl": False}
    return {}


def _resolve_remote_pg_host(host: str) -> str:
    """
    Внутри Docker localhost — это контейнер приложения, а не Postgres.
    Если задан DOCKER_PG_HOST (например postgres), подменяем им localhost/127.0.0.1.
    """
    h = (host or "").strip()
    alt = (os.environ.get("DOCKER_PG_HOST") or "").strip()
    if not alt:
        return h
    if h.lower() in ("localhost", "127.0.0.1", "::1"):
        return alt
    return h


class UserService:
    """Сервис управления пользователями"""
    
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)
    
    async def create_user(self, username: str, email: str, password: str, 
                          full_name: str = "", role: str = "viewer") -> User:
        """Создание нового пользователя"""
        # Проверяем уникальность
        existing = await self.repo.get_by_username(username)
        if existing:
            raise ValueError(f"Пользователь {username} уже существует")
        
        existing = await self.repo.get_by_email(email)
        if existing:
            raise ValueError(f"Email {email} уже используется")
        
        # Хешируем пароль
        password_hash = pwd_context.hash(password)
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            is_active=True
        )
        
        return await self.repo.create(user)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = await self.repo.get_by_username(username)
        if not user:
            return None
        
        if not pwd_context.verify(password, user.password_hash):
            return None
        
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        return await self.repo.get_by_id(user_id)

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение всех пользователей"""
        return await self.repo.get_all(skip, limit)

    async def count_users(self) -> int:
        return await self.repo.count_all()

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Обновление пользователя"""
        user = await self.repo.get_by_id(user_id)
        if not user:
            return None
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return user
        return await self.repo.update(user_id, user.model_copy(update=updates))
    
    async def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя"""
        return await self.repo.delete(user_id)


class DatabaseService:
    """Сервис управления подключениями к БД"""

    ALLOWED_PRIVILEGES = frozenset(
        {
            "CONNECT",
            "USAGE",
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "TRUNCATE",
            "REFERENCES",
            "TRIGGER",
        }
    )
    TABLE_PRIVILEGES = frozenset(
        {"SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"}
    )

    def __init__(self, db: AsyncSession):
        self.repo = DatabaseRepository(db)

    @staticmethod
    def normalize_privileges_json(raw: Optional[str]) -> List[str]:
        """Парсинг JSON-массива привилегий; по умолчанию CONNECT + USAGE + SELECT."""
        default = ["CONNECT", "USAGE", "SELECT"]
        if not raw or not str(raw).strip():
            return list(default)
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                out = [str(x).upper().strip() for x in data if str(x).strip()]
                out = [p for p in out if p in DatabaseService.ALLOWED_PRIVILEGES]
                return sorted(set(out)) if out else list(default)
        except (json.JSONDecodeError, TypeError):
            pass
        return list(default)

    @staticmethod
    def privileges_json_string(privileges: List[str]) -> str:
        return json.dumps(sorted(set(privileges)), ensure_ascii=False)

    async def create_database(
        self,
        name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database_name: str,
        owner_id: int,
        access_privileges: Optional[str] = None,
    ) -> Database:
        """Создание подключения к БД"""
        database = Database(
            name=name,
            host=host,
            port=port,
            username=username,
            password=password,
            database_name=database_name,
            owner_id=owner_id,
            status="disconnected",
            access_privileges=access_privileges,
        )

        return await self.repo.create(database)

    async def create_postgresql_database_if_missing(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        new_database: str,
        maintenance_database: str = "postgres",
    ) -> str:
        """
        Подключиться к служебной базе (по умолчанию postgres) и выполнить CREATE DATABASE,
        если базы с таким datname ещё нет. Нужны права CREATEDB или суперпользователь.
        """
        new_db = _validate_pg_new_db_name(new_database)
        maint_db = _validate_pg_new_db_name(maintenance_database)
        rh = _resolve_remote_pg_host(host)
        conn = None
        try:
            conn = await asyncpg.connect(
                host=rh,
                port=port,
                user=username,
                password=password,
                database=maint_db,
                timeout=30,
                **_asyncpg_ssl_kw(),
            )
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                new_db,
            )
            if exists:
                return new_db
            await conn.execute(f"CREATE DATABASE {new_db}")
            return new_db
        except ConnectionRefusedError as e:
            raise RuntimeError(
                "Не удалось подключиться к PostgreSQL (отказ в соединении). "
                "В Docker укажите хост сервиса — обычно postgres, а не localhost; "
                "либо задайте DOCKER_PG_HOST=postgres в окружении контейнера приложения."
            ) from e
        except asyncpg.InvalidPasswordError as e:
            raise RuntimeError("Неверный логин или пароль при подключении к серверу PostgreSQL.") from e
        except asyncpg.InvalidCatalogNameError as e:
            raise RuntimeError(
                f"Не удалось подключиться к административной базе «{maint_db}». "
                "Укажите существующую базу (часто postgres), к которой разрешён вход."
            ) from e
        except asyncpg.PostgresError as e:
            raise RuntimeError(
                f"PostgreSQL: {e.__class__.__name__}: {getattr(e, 'message', str(e))}"
            ) from e
        finally:
            if conn is not None:
                await conn.close()

    async def apply_database_role_privileges(
        self,
        host: str,
        port: int,
        admin_user: str,
        admin_password: str,
        database_name: str,
        grantee_role: str,
        privileges: List[str],
        maintenance_database: str = "postgres",
    ) -> None:
        """
        Выдать роли grantee_role привилегии на указанной БД (от имени admin_*).
        CONNECT — на уровне БД; USAGE/таблицы/последовательности — в public.
        """
        db = _validate_pg_new_db_name(database_name)
        maint = _validate_pg_new_db_name(maintenance_database)
        rh = _resolve_remote_pg_host(host)
        privs = sorted(
            {
                p.upper()
                for p in privileges
                if p and str(p).upper().strip() in self.ALLOWED_PRIVILEGES
            }
        )
        if not privs:
            return

        conn_maint: Optional[asyncpg.Connection] = None
        conn_db: Optional[asyncpg.Connection] = None
        try:
            conn_maint = await asyncpg.connect(
                host=rh,
                port=port,
                user=admin_user,
                password=admin_password,
                database=maint,
                timeout=30,
                **_asyncpg_ssl_kw(),
            )
            grantee_q = await conn_maint.fetchval(
                "SELECT quote_ident($1::text)", grantee_role
            )
            if "CONNECT" in privs:
                await conn_maint.execute(
                    f"GRANT CONNECT ON DATABASE {db} TO {grantee_q}"
                )

            table_privs = [p for p in privs if p in self.TABLE_PRIVILEGES]
            schema_needed = "USAGE" in privs or bool(table_privs) or "SELECT" in privs

            if schema_needed:
                await conn_maint.close()
                conn_maint = None
                conn_db = await asyncpg.connect(
                    host=rh,
                    port=port,
                    user=admin_user,
                    password=admin_password,
                    database=db,
                    timeout=30,
                    **_asyncpg_ssl_kw(),
                )
                gq = await conn_db.fetchval(
                    "SELECT quote_ident($1::text)", grantee_role
                )
                sp = await conn_db.fetchval(
                    "SELECT quote_ident($1::text)", "public"
                )
                await conn_db.execute(f"GRANT USAGE ON SCHEMA {sp} TO {gq}")
                if table_privs:
                    priv_sql = ", ".join(table_privs)
                    await conn_db.execute(
                        f"GRANT {priv_sql} ON ALL TABLES IN SCHEMA {sp} TO {gq}"
                    )
                    await conn_db.execute(
                        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {sp} "
                        f"GRANT {priv_sql} ON TABLES TO {gq}"
                    )
                if "SELECT" in privs:
                    await conn_db.execute(
                        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {sp} TO {gq}"
                    )
                    await conn_db.execute(
                        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {sp} "
                        f"GRANT SELECT ON SEQUENCES TO {gq}"
                    )
        except ConnectionRefusedError as e:
            raise RuntimeError(
                "Не удалось подключиться к PostgreSQL при выдаче прав (отказ в соединении)."
            ) from e
        except asyncpg.PostgresError as e:
            raise RuntimeError(
                f"PostgreSQL при выдаче прав: {e.__class__.__name__}: "
                f"{getattr(e, 'message', str(e))}"
            ) from e
        finally:
            if conn_maint is not None:
                await conn_maint.close()
            if conn_db is not None:
                await conn_db.close()

    async def test_connection(self, host: str, port: int, username: str, 
                             password: str, database_name: str) -> bool:
        """Тестирование подключения к БД"""
        try:
            conn = await asyncpg.connect(
                host=_resolve_remote_pg_host(host),
                port=port,
                user=username,
                password=password,
                database=database_name,
                timeout=5,
                **_asyncpg_ssl_kw(),
            )
            await conn.close()
            return True
        except Exception as e:
            return False
    
    async def get_database(self, db_id: int) -> Optional[Database]:
        """Получение подключения по ID"""
        return await self.repo.get_by_id(db_id)
    
    async def get_user_databases(self, owner_id: int, skip: int = 0, 
                                limit: int = 100) -> List[Database]:
        """Получение всех БД пользователя"""
        return await self.repo.get_by_owner(owner_id, skip, limit)
    
    async def get_all_databases(self, skip: int = 0, limit: int = 100) -> List[Database]:
        """Получение всех БД"""
        return await self.repo.get_all(skip, limit)

    async def count_databases(self) -> int:
        return await self.repo.count_all()

    async def count_connected_databases(self) -> int:
        return await self.repo.count_by_status("connected")
    
    async def update_database_status(self, db_id: int, status: str, 
                                     error: str = None) -> Optional[Database]:
        """Обновление статуса подключения"""
        database = await self.repo.get_by_id(db_id)
        if database:
            database.status = status
            database.last_checked = datetime.now(timezone.utc)
            return await self.repo.update(db_id, database)
        return None
    
    async def delete_database(self, db_id: int) -> bool:
        """Удаление подключения"""
        return await self.repo.delete(db_id)

    async def get_live_metrics(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database_name: str,
    ) -> dict:
        """
        Метрики с живого PostgreSQL (размер текущей БД, сессии).
        Свободное место на диске ОС через обычный SQL недоступно — только объём данных в кластере.
        """
        out: dict = {
            "reachable": False,
            "database_size_bytes": None,
            "active_backends": None,
            "pg_version": None,
            "error": None,
        }
        try:
            conn = await asyncpg.connect(
                host=_resolve_remote_pg_host(host),
                port=port,
                user=username,
                password=password,
                database=database_name,
                timeout=5,
                **_asyncpg_ssl_kw(),
            )
            out["reachable"] = True
            out["database_size_bytes"] = int(
                await conn.fetchval("SELECT pg_database_size(current_database())")
            )
            out["active_backends"] = int(
                await conn.fetchval(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                )
            )
            ver = await conn.fetchval("SELECT version()")
            out["pg_version"] = (ver or "")[:120]
            await conn.close()
        except Exception as e:
            out["error"] = str(e)[:500]
        return out

    async def backup_database_to_file(self, database: Database) -> Tuple[str, int]:
        """
        pg_dump в SQL-файл. Каталог: BACKUP_DIR или /tmp/app_backups (надёжнее при Docker + bind-mount на Windows).
        Требует postgresql-client в образе. PGSSLMODE по умолчанию disable (как у типичного dev Postgres без TLS).
        """
        if not shutil.which("pg_dump"):
            raise RuntimeError(
                "Утилита pg_dump не найдена в PATH. Пересоберите образ с пакетом postgresql-client (см. Dockerfile)."
            )
        if database.id is None:
            raise RuntimeError("Нет id подключения")

        backup_dir = os.environ.get("BACKUP_DIR") or "/tmp/app_backups"
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Не удалось создать каталог для бэкапов {backup_dir}: {e}") from e

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        fname = f"db_{database.id}_{ts}.sql"
        out_path = os.path.join(backup_dir, fname)

        # Параметры подключения только через env — так надёжнее для паролей со спецсимволами, чем argv.
        env = {
            **os.environ,
            "PGPASSWORD": database.password,
            "PGHOST": str(_resolve_remote_pg_host(database.host)),
            "PGPORT": str(database.port),
            "PGUSER": database.username,
            "PGDATABASE": database.database_name,
            "PGSSLMODE": os.environ.get("PGSSLMODE", "disable"),
        }
        cmd = [
            "pg_dump",
            "-w",
            "-F",
            "p",
            "--no-owner",
            "-f",
            out_path,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as e:
            raise RuntimeError("Команда pg_dump не запущена (нет бинарника).") from e

        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace")[:4000]
            logger.warning("pg_dump failed rc=%s stderr=%s", proc.returncode, err)
            if os.path.isfile(out_path):
                try:
                    os.remove(out_path)
                except OSError:
                    pass
            raise RuntimeError(
                err.strip() or f"pg_dump завершился с кодом {proc.returncode}. "
                f"Проверьте хост из контейнера (часто нужно имя сервиса postgres, а не localhost), "
                f"учётные данные и переменную PGSSLMODE (для TLS: prefer или require)."
            )
        try:
            size = os.path.getsize(out_path)
        except OSError as e:
            raise RuntimeError(f"Дамп создан, но не удалось прочитать размер файла: {e}") from e
        return fname, size
    
    async def get_database_tables(self, host: str, port: int, username: str,
                                 password: str, database_name: str,
                                 schema: str = 'public') -> List[dict]:
        """Получение списка таблиц из БД"""
        try:
            schema = _validate_identifier(schema)
            conn = await asyncpg.connect(
                host=_resolve_remote_pg_host(host),
                port=port,
                user=username,
                password=password,
                database=database_name,
                **_asyncpg_ssl_kw(),
            )
            
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = $1
                ORDER BY tablename
            """, schema)
            
            await conn.close()
            return [{"name": t['tablename']} for t in tables]
        except Exception as e:
            raise Exception(f"Ошибка получения таблиц: {str(e)}")

    async def get_database_schemas(self, host: str, port: int, username: str,
                                  password: str, database_name: str) -> List[dict]:
        """Получение списка схем из БД"""
        try:
            conn = await asyncpg.connect(
                host=_resolve_remote_pg_host(host),
                port=port,
                user=username,
                password=password,
                database=database_name,
                **_asyncpg_ssl_kw(),
            )
            # template0/template1 — это отдельные *базы* кластера, не схемы внутри БД.
            # Скрываем только служебные схемы PostgreSQL; public и пользовательские остаются.
            schemas = await conn.fetch("""
                SELECT nspname FROM pg_namespace
                WHERE nspname NOT IN ('pg_catalog', 'information_schema')
                  AND nspname NOT LIKE 'pg_toast%'
                  AND nspname NOT LIKE 'pg_temp%'
                ORDER BY nspname
            """)
            await conn.close()
            return [{"name": s['nspname']} for s in schemas]
        except Exception as e:
            raise Exception(f"Ошибка получения схем: {str(e)}")

    async def get_table_columns(self, host: str, port: int, username: str,
                                password: str, database_name: str,
                                schema: str, table_name: str) -> List[dict]:
        """Получение описания колонок таблицы"""
        try:
            schema = _validate_identifier(schema)
            table_name = _validate_identifier(table_name)
            conn = await asyncpg.connect(
                host=_resolve_remote_pg_host(host),
                port=port,
                user=username,
                password=password,
                database=database_name,
                **_asyncpg_ssl_kw(),
            )
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
            """, schema, table_name)
            await conn.close()
            return [
                {
                    "name": c['column_name'],
                    "type": c['data_type'],
                    "nullable": c['is_nullable'],
                    "default": c['column_default']
                }
                for c in columns
            ]
        except Exception as e:
            raise Exception(f"Ошибка получения схемы таблицы: {str(e)}")

    async def get_table_rows(self, host: str, port: int, username: str,
                             password: str, database_name: str,
                             schema: str, table_name: str,
                             limit: int = 50, offset: int = 0) -> List[dict]:
        """Получение строк из таблицы с пагинацией"""
        try:
            schema = _validate_identifier(schema)
            table_name = _validate_identifier(table_name)
            conn = await asyncpg.connect(
                host=_resolve_remote_pg_host(host),
                port=port,
                user=username,
                password=password,
                database=database_name,
                **_asyncpg_ssl_kw(),
            )
            query = f'SELECT * FROM "{schema}"."{table_name}" LIMIT $1 OFFSET $2'
            rows = await conn.fetch(query, limit, offset)
            await conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка получения данных таблицы: {str(e)}")

    async def get_table_count(self, host: str, port: int, username: str,
                              password: str, database_name: str,
                              schema: str, table_name: str) -> int:
        """Получение количества строк в таблице"""
        try:
            schema = _validate_identifier(schema)
            table_name = _validate_identifier(table_name)
            conn = await asyncpg.connect(
                host=_resolve_remote_pg_host(host),
                port=port,
                user=username,
                password=password,
                database=database_name,
                **_asyncpg_ssl_kw(),
            )
            query = f'SELECT count(*) as total FROM "{schema}"."{table_name}"'
            row = await conn.fetchrow(query)
            await conn.close()
            return row['total'] if row else 0
        except Exception as e:
            raise Exception(f"Ошибка получения количества строк: {str(e)}")

    async def list_server_catalog_databases(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        maintenance_database: str = "postgres",
    ) -> List[dict]:
        """Имена баз в кластере (datistemplate = false), подключение к maintenance_database."""
        maint_db = _validate_pg_new_db_name(maintenance_database)
        rh = _resolve_remote_pg_host(host)
        conn = None
        try:
            conn = await asyncpg.connect(
                host=rh,
                port=port,
                user=username,
                password=password,
                database=maint_db,
                timeout=15,
                **_asyncpg_ssl_kw(),
            )
            rows = await conn.fetch(
                """
                SELECT d.datname AS name,
                       pg_database_size(d.datname) AS size_bytes
                FROM pg_database d
                WHERE NOT d.datistemplate
                ORDER BY d.datname
                """
            )
            return [
                {
                    "name": r["name"],
                    "database_size_bytes": int(r["size_bytes"])
                    if r["size_bytes"] is not None
                    else None,
                }
                for r in rows
            ]
        finally:
            if conn is not None:
                await conn.close()


class QueryLogService:
    """Сервис логирования запросов"""
    
    def __init__(self, db: AsyncSession):
        self.repo = QueryLogRepository(db)
    
    async def log_query(self, user_id: int, database_id: int, query_text: str,
                       status: str = "success", error_message: str = None,
                       execution_time_ms: float = 0.0) -> QueryLog:
        """Логирование запроса"""
        log = QueryLog(
            user_id=user_id,
            database_id=database_id,
            query_text=query_text,
            status=status,
            error_message=error_message,
            execution_time_ms=execution_time_ms
        )
        return await self.repo.create(log)
    
    async def get_database_logs(self, database_id: int, skip: int = 0, 
                               limit: int = 100) -> List[QueryLog]:
        """Получение логов БД"""
        return await self.repo.get_by_database(database_id, skip, limit)
    
    async def get_user_logs(self, user_id: int, skip: int = 0, 
                           limit: int = 100) -> List[QueryLog]:
        """Получение логов пользователя"""
        return await self.repo.get_by_user(user_id, skip, limit)

    async def get_all_logs(self, skip: int = 0, limit: int = 100) -> List[QueryLog]:
        """Все логи запросов"""
        return await self.repo.get_all(skip, limit)


class AdminService:
    """Административный сервис"""
    
    def __init__(self, db: AsyncSession):
        self.user_service = UserService(db)
        self.db_service = DatabaseService(db)
    
    async def get_system_statistics(self) -> dict:
        """Получение статистики системы"""
        total_users = await self.user_service.count_users()
        total_databases = await self.db_service.count_databases()
        active = await self.db_service.count_connected_databases()
        return {
            "total_users": total_users,
            "total_databases": total_databases,
            "active_connections": active,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_user_dashboard(self, owner_id: int) -> dict:
        """Дашборд: сводка + метрики по каждому сохранённому подключению пользователя.

        Для каждой записи параллельно опрашиваются:
        - метрики по сохранённой БД (имя из записи) — могут быть недоступны;
        - каталог кластера через подключение к служебной БД postgres — список имён БД
          в кластере на момент запроса, часто доступен даже когда целевая БД недоступна.
        """
        summary = await self.get_system_statistics()
        dbs = await self.db_service.get_user_databases(owner_id, 0, 200)

        async def _safe_cluster_catalog(d: Database) -> dict:
            try:
                rows = await self.db_service.list_server_catalog_databases(
                    d.host, d.port, d.username, d.password, "postgres"
                )
                return {"ok": True, "databases": rows, "error": None}
            except Exception as e:
                return {"ok": False, "databases": [], "error": str(e)[:500]}

        async def _dashboard_row(d: Database) -> Tuple[Database, dict, dict]:
            m, cat = await asyncio.gather(
                self.db_service.get_live_metrics(
                    d.host, d.port, d.username, d.password, d.database_name
                ),
                _safe_cluster_catalog(d),
            )
            return d, m, cat

        triples = await asyncio.gather(*[_dashboard_row(d) for d in dbs])
        connections = []
        total_remote = 0
        reachable = 0
        catalog_ok = 0
        cluster_catalogs = {}
        for d, m, cat in triples:
            if m.get("reachable"):
                reachable += 1
            if cat.get("ok"):
                catalog_ok += 1
                catalog_key = (d.host, d.port, d.username, d.password)
                if catalog_key not in cluster_catalogs:
                    cluster_catalogs[catalog_key] = cat
            connections.append(
                {
                    "id": d.id,
                    "name": d.name,
                    "host": d.host,
                    "port": d.port,
                    "database_name": d.database_name,
                    "status": d.status,
                    "access_privileges": d.access_privileges,
                    "metrics": m,
                    "cluster_catalog": cat,
                }
            )
        for cat in cluster_catalogs.values():
            for row in cat.get("databases", []):
                sz = row.get("database_size_bytes")
                if isinstance(sz, int):
                    total_remote += sz
        summary["remote_databases_total_bytes"] = total_remote
        summary["remote_databases_reachable_count"] = reachable
        summary["your_databases_count"] = len(connections)
        summary["cluster_catalogs_ok_count"] = catalog_ok
        summary["cluster_databases_total_count"] = sum(
            len(cat.get("databases", [])) for cat in cluster_catalogs.values()
        )
        return {"summary": summary, "connections": connections}
