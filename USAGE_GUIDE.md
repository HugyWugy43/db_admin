# ИНСТРУКЦИИ ПО ЗАПУСКУ И ИСПОЛЬЗОВАНИЮ

## Содержание

1. [Предварительные требования](#предварительные-требования)
2. [Первоначальная установка](#первоначальная-установка)
3. [Запуск приложения](#запуск-приложения)
4. [Использование приложения](#использование-приложения)
5. [Администрирование](#администрирование)
6. [Решение проблем](#решение-проблем)
7. [Остановка и очистка](#остановка-и-очистка)

---

## Предварительные требования

### Для локального развертывания

- **Docker** версии 20.10 или выше
- **Docker Compose** версии 1.29 или выше
- **Git** (для клонирования репозитория)
- **4 ГБ оперативной памяти** (минимум)
- **2 ГБ свободного дискового пространства**

### Проверка установки

```bash
# Проверить Docker
docker --version
# Выведет: Docker version 20.10.x

# Проверить Docker Compose
docker-compose --version
# Выведет: Docker Compose version 1.29.x

# Проверить Git
git --version
# Выведет: git version 2.x.x
```

---

## Первоначальная установка

### Шаг 1: Клонирование репозитория

```bash
# Клонировать репозиторий
git clone https://github.com/your-username/course_backend.git

# Перейти в директорию проекта
cd course_backend
```

### Шаг 2: Создание файла переменных окружения

```bash
# Скопировать пример файла
cp .env.example .env

# (Опционально) Отредактировать значения
# nano .env  # или используйте ваш редактор
```

**Значения по умолчанию достаточны для локального запуска.**

### Шаг 3: Проверка структуры проекта

```bash
# Проверить наличие ключевых файлов
ls -la
# Должны быть: docker-compose.yml, Dockerfile, requirements.txt, .env

# Проверить структуру папок
tree app/
# или
ls -R app/
```

---

## Запуск приложения

### Способ 1: Полный запуск с Docker Compose (Рекомендуется)

```bash
# 1. Построить Docker образы
docker-compose build

# 2. Запустить все сервисы в фоновом режиме
docker-compose up -d

# 3. Проверить статус контейнеров
docker-compose ps
# Выведет список всех сервисов и их статус

# 4. Просмотреть логи приложения
docker-compose logs -f app

# 5. Ожидайте пока приложение полностью запустится
# (примерно 5-10 секунд)
```

**Выходные данные docker-compose ps:**
```
NAME                  COMMAND                  STATUS
db_admin_postgres    "docker-entrypoint.s..."  Up
db_admin_redis       "redis-server"           Up
db_admin_app         "uvicorn app.main:app"   Up
```

### Способ 2: Пошаговый запуск

```bash
# Запустить только БД
docker-compose up -d postgres redis

# Дождаться запуска БД (10-15 секунд)
sleep 15

# Запустить приложение
docker-compose up -d app

# Проверить логи
docker-compose logs app
```

### Первоначальная инициализация БД

После первого запуска нужно применить миграции:

```bash
# Применить все миграции Alembic
docker-compose exec app alembic upgrade head

# Проверить результат
docker-compose exec app alembic current
# Выведет: (head), 2024-01-01 12:00:00
```

### Проверка что все работает

```bash
# Проверить API
curl http://localhost:8000/

# Проверить статус БД
docker-compose exec postgres pg_isready

# Проверить Redis
docker-compose exec redis redis-cli ping
# Выведет: PONG
```

---

## Использование приложения

### Доступ к приложению

После запуска откройте браузер и перейдите по следующим адресам:

| Ресурс | URL |
|--------|-----|
| **Главное приложение** | http://localhost:8000/static/index.html |
| **API Документация (Swagger)** | http://localhost:8000/docs |
| **GraphQL Playground** | http://localhost:8000/graphql |
| **ReDoc документация** | http://localhost:8000/redoc |

### Первый вход

1. **Откройте приложение** http://localhost:8000/static/index.html
2. **Нажмите** на вкладку "Регистрация"
3. **Заполните форму:**
   - Имя пользователя: `admin`
   - Email: `admin@example.com`
   - Пароль: `admin123456`
   - Полное имя: `Administrator`
4. **Нажмите** кнопку "Зарегистрироваться"
5. **Вернитесь** на вкладку "Вход"
6. **Введите** учетные данные и нажмите "Войти"

### Основные возможности

#### 1. Дашборд
- Просмотр статистики (кол-во пользователей, БД)
- Список последних добавленных БД
- Быстрые статистики

#### 2. Управление БД
1. Нажмите **"🗃️ Базы данных"** в меню
2. Нажмите **"+ Добавить новую БД"**
3. Заполните данные подключения:
   - **Название**: дайте имя подключению
   - **Хост**: адрес сервера БД (например: db.example.com)
   - **Порт**: порт PostgreSQL (обычно 5432)
   - **Имя пользователя**: пользователь БД
   - **Пароль**: пароль
   - **Название БД**: имя конкретной БД
4. Нажмите **"Добавить"**

#### 3. Тестирование подключения
1. На карточке БД нажмите кнопку **"Тест"**
2. Если подключение успешно, вы увидите сообщение "Подключение успешно!"
3. Статус изменится на "connected" (зеленый)

#### 4. Просмотр таблиц
1. Нажмите кнопку **"Таблицы"** на карточке БД
2. Увидите список всех таблиц в этой БД

#### 5. Просмотр логов
1. Нажмите **"📋 Логи"** в меню
2. Увидите историю всех выполненных операций

#### 6. Управление профилем
1. Нажмите **"⚙️ Настройки"** в меню
2. Отредактируйте свой профиль:
   - Email
   - Полное имя
3. Нажмите **"Сохранить"**

### Примеры REST API запросов

```bash
# 1. Регистрация нового пользователя
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&email=john@example.com&password=secure123&full_name=John Doe"

# 2. Вход пользователя
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=secure123"
# Результат будет содержать: access_token, token_type, user_id

# 3. Получить информацию о текущем пользователе
# (замените 1 на реальный user_id)
curl -X GET "http://localhost:8000/api/auth/me?user_id=1" \
  -H "Authorization: Bearer <your_token>"

# 4. Получить список пользователей
curl -X GET "http://localhost:8000/api/users/" \
  -H "Authorization: Bearer <your_token>"

# 5. Создать новое подключение к БД
curl -X POST "http://localhost:8000/api/admin/databases" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Bearer <your_token>" \
  -d "name=MyDatabase&host=localhost&port=5432&username=admin&password=admin123&database_name=mydb&owner_id=1"

# 6. Получить список БД пользователя
curl -X GET "http://localhost:8000/api/admin/databases?owner_id=1" \
  -H "Authorization: Bearer <your_token>"

# 7. Получить БД по ID
curl -X GET "http://localhost:8000/api/admin/databases/1" \
  -H "Authorization: Bearer <your_token>"

# 8. Тестировать подключение к БД
curl -X POST "http://localhost:8000/api/admin/databases/1/test-connection" \
  -H "Authorization: Bearer <your_token>"

# 9. Получить таблицы БД
curl -X GET "http://localhost:8000/api/admin/databases/1/tables" \
  -H "Authorization: Bearer <your_token>"

# 10. Удалить БД
curl -X DELETE "http://localhost:8000/api/admin/databases/1" \
  -H "Authorization: Bearer <your_token>"
```

### Примеры GraphQL запросов

Откройте http://localhost:8000/graphql

```graphql
# 1. Получить список пользователей
query {
  listUsers(skip: 0, limit: 10) {
    id
    username
    email
    role
    isActive
    createdAt
  }
}

# 2. Получить список БД
query {
  listDatabases(skip: 0, limit: 10) {
    id
    name
    host
    port
    databaseName
    status
    createdAt
  }
}

# 3. Получить таблицы БД
query {
  getTables(databaseId: 1) {
    id
    name
    rowCount
    sizeBytes
  }
}

# 4. Получить логи запросов
query {
  getQueryLogs(databaseId: 1, limit: 50) {
    id
    queryText
    status
    executionTimeMs
    createdAt
  }
}

# 5. Создать пользователя (мутация)
mutation {
  createUser(username: "newuser", email: "user@example.com", password: "pass123") {
    id
    username
    email
    createdAt
  }
}

# 6. Создать подключение к БД (мутация)
mutation {
  createDatabase(
    name: "Production DB"
    host: "db.prod.example.com"
    port: 5432
    username: "prod_user"
    password: "prod_password"
    databaseName: "production"
  ) {
    id
    name
    status
  }
}

# 7. Тестировать подключение (мутация)
mutation {
  testDatabaseConnection(
    host: "localhost"
    port: 5432
    username: "test"
    password: "test"
    databaseName: "testdb"
  )
}
```

---

## Администрирование

### Управление контейнерами

```bash
# Просмотреть статус всех контейнеров
docker-compose ps

# Просмотреть логи приложения (в реальном времени)
docker-compose logs -f app

# Просмотреть логи БД
docker-compose logs -f postgres

# Просмотреть логи Redis
docker-compose logs -f redis

# Остановить приложение (но сохранить данные)
docker-compose stop app

# Перезагрузить приложение
docker-compose restart app

# Перезагрузить все сервисы
docker-compose restart

# Удалить контейнеры (данные в томах сохранятся)
docker-compose down

# Полная очистка (удалить все включая тома данных)
docker-compose down -v
```

### Доступ к БД напрямую

```bash
# Подключиться к PostgreSQL
docker-compose exec postgres psql -U admin -d db_admin

# Полезные SQL команды в psql:
# \dt - показать все таблицы
# \d <table> - показать структуру таблицы
# \l - показать все БД
# SELECT * FROM users; - вывести всех пользователей
# \q - выход

# Примеры:
docker-compose exec postgres psql -U admin -d db_admin -c "SELECT * FROM users;"
docker-compose exec postgres psql -U admin -d db_admin -c "SELECT COUNT(*) FROM users;"
```

### Доступ к Redis

```bash
# Подключиться к Redis
docker-compose exec redis redis-cli

# Полезные команды в redis-cli:
# PING - проверить соединение
# KEYS * - показать все ключи
# GET <key> - получить значение
# SET <key> <value> - установить значение
# DEL <key> - удалить ключ
# FLUSHALL - очистить все данные
# QUIT - выход

# Примеры:
docker-compose exec redis redis-cli PING
docker-compose exec redis redis-cli KEYS "*"
docker-compose exec redis redis-cli FLUSHALL
```

### Резервное копирование БД

```bash
# Создать бэкап PostgreSQL
docker-compose exec postgres pg_dump -U admin db_admin > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить бэкап
docker-compose exec -T postgres psql -U admin db_admin < backup_20240101_120000.sql
```

### Просмотр логов приложения

```bash
# Последние 50 строк логов
docker-compose logs --tail=50 app

# Логи за последний час
docker-compose logs --since=1h app

# Следить за логами в реальном времени (Ctrl+C для выхода)
docker-compose logs -f app

# Логи всех сервисов
docker-compose logs -f
```

---

## Решение проблем

### Проблема: Контейнеры не запускаются

```bash
# Решение 1: Проверить наличие образов
docker images

# Решение 2: Перестроить образы
docker-compose build --no-cache

# Решение 3: Проверить логи ошибок
docker-compose logs
```

### Проблема: Ошибка подключения к БД

```bash
# Проверить что PostgreSQL контейнер запущен
docker-compose ps postgres

# Проверить логи БД
docker-compose logs postgres

# Проверить что порт 5432 доступен
netstat -an | grep 5432

# Если уже занято, остановить другой контейнер
docker ps | grep 5432
docker stop <container_id>
```

### Проблема: Фронтенд не открывается

```bash
# Проверить что приложение запущено
docker-compose ps app

# Проверить логи приложения
docker-compose logs app

# Проверить что порт 8000 доступен
curl http://localhost:8000/

# Если ошибка Connection refused - приложение еще не запустилось
# Подождите 10 секунд и попробуйте снова
```

### Проблема: Ошибка при применении миграций

```bash
# Посмотреть какие миграции уже применены
docker-compose exec app alembic current

# Откатить последнюю миграцию
docker-compose exec app alembic downgrade -1

# Посмотреть статус всех миграций
docker-compose exec app alembic heads

# Переапплицировать все миграции
docker-compose exec app alembic upgrade head
```

### Проблема: Забыл пароль / нужно сбросить данные

```bash
# Полная очистка (ВНИМАНИЕ: удалит все данные)
docker-compose down -v

# Пересоздать контейнеры с нуля
docker-compose up -d

# Переапплицировать миграции
docker-compose exec app alembic upgrade head

# Теперь можно зарегистрироваться заново
```

### Проблема: Высокое использование памяти

```bash
# Проверить использование ресурсов
docker stats

# Очистить неиспользуемые образы и контейнеры
docker system prune -a

# Удалить том БД и пересоздать (очистит данные)
docker-compose down -v
docker-compose up -d
```

---

## Остановка и очистка

### Корректная остановка (сохраняет данные)

```bash
# Остановить все сервисы
docker-compose down

# Или
docker-compose stop

# Данные останутся в томах - их можно запустить снова
docker-compose up -d
```

### Полная очистка (удалит ВСЕ данные)

```bash
# ВНИМАНИЕ: Это удалит все данные БД и кэш Redis
docker-compose down -v

# Или более агрессивно
docker system prune -a --volumes
```

### Удаление отдельных компонентов

```bash
# Удалить только данные БД (Redis данные останутся)
docker volume rm course_backend_postgres_data

# Удалить только Redis данные
docker volume rm course_backend_redis_data

# Удалить конкретный контейнер
docker-compose rm -f app
```

---

## Полезные команды для разработки

```bash
# Запустить интерактивный shell в контейнере
docker-compose exec app bash

# Запустить Python интерпретатор
docker-compose exec app python

# Установить новую зависимость
docker-compose exec app pip install <package_name>
# (затем обновить requirements.txt вручную)

# Запустить тесты
docker-compose exec app pytest

# Проверить синтаксис Python
docker-compose exec app python -m py_compile app/main.py

# Запустить linter
docker-compose exec app pylint app/

# Отформатировать код
docker-compose exec app black app/
```

---

## Быстрые команды

```bash
# Запустить приложение
docker-compose up -d && sleep 5 && docker-compose exec app alembic upgrade head

# Остановить приложение
docker-compose down

# Перезагрузить приложение
docker-compose restart app

# Посмотреть статус
docker-compose ps

# Посмотреть логи
docker-compose logs -f

# Полная очистка
docker-compose down -v && docker system prune -a
```

---

**Если у вас остались вопросы, обратитесь к [README.md](./README.md) или посмотрите раздел "Решение проблем".**
