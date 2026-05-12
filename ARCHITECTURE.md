# Архитектурные Диаграммы

## 1. Архитектура приложения (слои)

```
┌────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                          │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  REST API    │  │   GraphQL    │  │  Static Files    │    │
│  │  /api/*      │  │  /graphql    │  │  /static         │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                             ↑↓
┌────────────────────────────────────────────────────────────────┐
│                   Application Layer                            │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ UserService  │  │DatabaseService│ │QueryLogService   │    │
│  │              │  │               │  │                  │    │
│  │- create_user │  │- create_db    │  │- log_query       │    │
│  │- auth_user   │  │- test_connect │  │- get_logs        │    │
│  │- get_user    │  │- get_tables   │  │                  │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                             ↑↓
┌────────────────────────────────────────────────────────────────┐
│                    Domain Layer                                │
│                                                                │
│  Entities (Pydantic models):                                  │
│  - User, Database, Table, Column, Index                       │
│  - QueryLog, BackupLog                                        │
│                                                                │
│  Business Rules (не зависит от БД и фреймворка)             │
└────────────────────────────────────────────────────────────────┘
                             ↑↓
┌────────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                           │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │UserRepository│  │DatabaseRepo  │  │QueryLogRepository│    │
│  │              │  │              │  │                  │    │
│  │- create      │  │- create      │  │- create          │    │
│  │- get_by_id   │  │- get_by_id   │  │- get_by_database │    │
│  │- get_all     │  │- get_by_owner│  │- get_by_user     │    │
│  │- update      │  │- update      │  │                  │    │
│  │- delete      │  │- delete      │  │                  │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                             ↑↓
┌────────────────────────────────────────────────────────────────┐
│                    Data Access Layer                           │
│                                                                │
│  SQLAlchemy ORM:                                              │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ UserModel | DatabaseModel | TableModel | ColumnModel  │   │
│  │ IndexModel | QueryLogModel | BackupLogModel           │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                             ↑↓
┌────────────────────────────────────────────────────────────────┐
│                   External Services                            │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ PostgreSQL   │  │    Redis     │  │  asyncpg (driver)│    │
│  │   Port 5432  │  │  Port 6379   │  │                  │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

## 2. Диаграмма потока данных

```
┌─────────────────┐
│   Пользователь │
└────────┬────────┘
         │
         ↓ (HTTP Request)
┌─────────────────────────────────────┐
│  FastAPI Application                │
│  - CORS Middleware                  │
│  - Request validation               │
└────────┬────────────────────────────┘
         │
         ├─→ REST API Router          → Service → Repository → ORM → DB
         │
         ├─→ GraphQL Router           → Service → Repository → ORM → DB
         │
         └─→ Static Files Middleware  → Frontend

         ↓ (Response)
┌─────────────────────────────────────┐
│  JSON Response / GraphQL Result      │
└─────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  Frontend (JavaScript)              │
│  - DOM Updates                      │
│  - User Interface                   │
└─────────────────────────────────────┘
```

## 3. Диаграмма базы данных

```
┌──────────────────┐
│      users       │
├──────────────────┤
│ id (PK)          │
│ username (UNIQUE)│
│ email (UNIQUE)   │
│ full_name        │
│ hashed_password  │
│ role             │
│ is_active        │
│ created_at       │
│ updated_at       │
└────────┬─────────┘
         │ (1:N)
         │
    ┌────┴────┐
    │          │
    ↓          ↓
┌──────────────────┐
│   databases      │
├──────────────────┤
│ id (PK)          │
│ name             │
│ host             │
│ port             │
│ username         │
│ password         │
│ database_name    │
│ status           │
│ owner_id (FK→users)
│ created_at       │
│ updated_at       │
│ last_checked     │
└────────┬─────────┘
         │ (1:N)
         │
         ↓
┌──────────────────┐
│     tables       │
├──────────────────┤
│ id (PK)          │
│ name             │
│ database_id (FK) │
│ row_count        │
│ size_bytes       │
│ created_at       │
│ updated_at       │
└────────┬─────────┘
         │ (1:N)
         │
    ┌────┴────┐
    │          │
    ↓          ↓
┌──────────────────┐
│    columns       │
├──────────────────┤
│ id (PK)          │
│ name             │
│ table_id (FK)    │
│ data_type        │
│ is_nullable      │
│ is_primary_key   │
│ is_unique        │
│ default_value    │
└──────────────────┘

┌──────────────────┐
│    indexes       │
├──────────────────┤
│ id (PK)          │
│ name             │
│ table_id (FK)    │
│ columns (JSON)   │
│ is_unique        │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│   query_logs     │
├──────────────────┤
│ id (PK)          │
│ user_id (FK)     │
│ database_id (FK) │
│ query_text       │
│ status           │
│ error_message    │
│ execution_time   │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│   backup_logs    │
├──────────────────┤
│ id (PK)          │
│ database_id (FK) │
│ user_id (FK)     │
│ backup_name      │
│ size_bytes       │
│ status           │
│ created_at       │
│ completed_at     │
└──────────────────┘
```

## 4. UML диаграмма классов (основные компоненты)

```
┌──────────────────────────────────────────────┐
│              UserService                     │
├──────────────────────────────────────────────┤
│ - repo: UserRepository                       │
├──────────────────────────────────────────────┤
│ + create_user(...)                           │
│ + authenticate_user(username, password)      │
│ + get_user(user_id)                          │
│ + get_all_users()                            │
│ + update_user(user_id, ...)                  │
│ + delete_user(user_id)                       │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│          DatabaseService                     │
├──────────────────────────────────────────────┤
│ - repo: DatabaseRepository                   │
├──────────────────────────────────────────────┤
│ + create_database(...)                       │
│ + test_connection(...)                       │
│ + get_database(db_id)                        │
│ + get_user_databases(owner_id)               │
│ + update_database_status(...)                │
│ + delete_database(db_id)                     │
│ + get_database_tables(...)                   │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│         UserRepository                       │
├──────────────────────────────────────────────┤
│ - db: AsyncSession                           │
├──────────────────────────────────────────────┤
│ + create(user)                               │
│ + get_by_id(user_id)                         │
│ + get_by_username(username)                  │
│ + get_by_email(email)                        │
│ + get_all(skip, limit)                       │
│ + update(user_id, user)                      │
│ + delete(user_id)                            │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│        DatabaseRepository                    │
├──────────────────────────────────────────────┤
│ - db: AsyncSession                           │
├──────────────────────────────────────────────┤
│ + create(database)                           │
│ + get_by_id(db_id)                           │
│ + get_by_owner(owner_id, ...)                │
│ + get_all(skip, limit)                       │
│ + update(db_id, database)                    │
│ + delete(db_id)                              │
└──────────────────────────────────────────────┘
```

## 5. Последовательность аутентификации

```
User        Browser         FastAPI         Database        Redis
 │              │               │               │              │
 │─ Register ──→│               │               │              │
 │              │─ POST /register──→             │              │
 │              │               │               │              │
 │              │               ├─ Create user ─→             │
 │              │               │               │              │
 │              │               │←─ User created ─             │
 │              │←─ 200 OK ──────               │              │
 │              │               │               │              │
 │─ Login ──────→               │               │              │
 │              │─ POST /login────→              │              │
 │              │               │               │              │
 │              │               ├─ Find user ───→             │
 │              │               │               │              │
 │              │               │←─ User found ─              │
 │              │               │               │              │
 │              │               ├─ Verify password            │
 │              │               │               │              │
 │              │               ├─ Generate JWT               │
 │              │               │               │              │
 │              │←─ {token} ─────               │              │
 │              │               │               │              │
 │─ Request ────→               │               │              │
 │ (with token) │               │               │              │
 │              │─ GET /api/* ───→              │              │
 │              │ Auth: Bearer   │               │              │
 │              │ {token}        ├─ Verify JWT ─│─ Check cache ─→
 │              │               │               │←─ Valid? ─────
 │              │               │               │              │
 │              │←─ {data} ──────               │              │
 │              │               │               │              │
```

## 6. Последовательность работы с БД

```
User        Frontend        API             Service         Database
 │              │            │               │               │
 │─ Add DB ─────→            │               │               │
 │              │            │               │               │
 │              │─ POST /api/admin/databases─→               │
 │              │            │               │               │
 │              │            ├─ create_database()            │
 │              │            │               │               │
 │              │            │          ├─ Validate         │
 │              │            │          │                   │
 │              │            │          ├─ Create ORM model │
 │              │            │          │                   │
 │              │            │          ├─ Save to DB ─────→
 │              │            │          │                   │
 │              │            │          │←─ Database saved ─│
 │              │            │←─ Database object ─│          │
 │              │←─ {db_info}─               │               │
 │              │            │               │               │
 │─ Test Conn ──→            │               │               │
 │              │─ POST test-connection─→     │               │
 │              │            │               │               │
 │              │            ├─ test_connection()            │
 │              │            │               │               │
 │              │            │          ├─ asyncpg.connect()│
 │              │            │          │                   │
 │              │            │          ├─ Connect DB ─────→
 │              │            │          │                   │
 │              │            │          │←─ Connected ─────│
 │              │            │          │                   │
 │              │            │          ├─ Update status ──→
 │              │            │←─ success ────                │
 │              │←─ {success}─               │               │
 │              │            │               │               │
```

## 7. Диаграмма развертывания

```
┌─────────────────────────────────────────────────────────┐
│              Docker Host / Server                        │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           docker-compose                         │  │
│  │                                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │  │
│  │  │ postgres │  │  redis   │  │   FastAPI    │   │  │
│  │  │ :5432    │  │  :6379   │  │   :8000      │   │  │
│  │  │  (DB)    │  │ (Cache)  │  │ (App)        │   │  │
│  │  └─────┬────┘  └────┬─────┘  └──────┬───────┘   │  │
│  │        │            │               │           │  │
│  │        └────────────┼───────────────┘           │  │
│  │                     │                           │  │
│  │  ┌──────────────────┴──────────────────┐        │  │
│  │  │     volumes (persistent data)      │        │  │
│  │  │  - postgres_data:/var/lib/...      │        │  │
│  │  └─────────────────────────────────────┘        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  Port mappings:                                         │
│  - 5432:5432 (PostgreSQL)                              │
│  - 6379:6379 (Redis)                                   │
│  - 8000:8000 (FastAPI)                                 │
└─────────────────────────────────────────────────────────┘
         ↑
         │ (HTTP/HTTPS)
         │
  ┌──────────────┐
  │    Client    │
  │   Browser    │
  └──────────────┘
```

## 8. Диаграмма взаимодействия компонентов

```
                    ┌─────────────────┐
                    │   Пользователь  │
                    └────────┬────────┘
                             │
                             ↓
                    ┌─────────────────┐
                    │   Frontend      │
                    │   (HTML/CSS/JS) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ↓              ↓              ↓
         ┌────────┐    ┌─────────┐    ┌─────────┐
         │  REST  │    │ GraphQL │    │ Static  │
         │  API   │    │         │    │ Files   │
         └────┬───┘    └────┬────┘    └────┬────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                            ↓
                    ┌─────────────────┐
                    │  FastAPI        │
                    │  Application    │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ↓                   ↓                   ↓
    ┌─────────┐         ┌──────────┐     ┌────────────┐
    │Services │         │Logging   │     │Middleware  │
    │         │         │          │     │(CORS, etc) │
    └────┬────┘         └──────────┘     └────────────┘
         │
         ├──→ UserService
         ├──→ DatabaseService
         ├──→ QueryLogService
         │
         ↓
    ┌─────────────────────┐
    │ Repositories        │
    │ - UserRepository    │
    │ - DatabaseRepository│
    │ - QueryLogRepository│
    └────────┬────────────┘
             │
             ↓
    ┌─────────────────────┐
    │  SQLAlchemy ORM     │
    │  - Models           │
    │  - AsyncSession     │
    └────────┬────────────┘
             │
        ┌────┼────┐
        │    │    │
        ↓    ↓    ↓
    ┌────┐ ┌─────┐ ┌──────┐
    │ DB │ │Cache│ │Logs  │
    │(PG)│ │Redis│ │Files │
    └────┘ └─────┘ └──────┘
```

