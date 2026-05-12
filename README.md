# DB Administrator - Веб-приложение для администрирования баз данных

🗄️ Полнофункциональное веб-приложение для управления, мониторинга и администрирования подключений к базам данных PostgreSQL.

## ✨ Особенности

- **Управление подключениями** - Добавляйте и управляйте подключениями к множеству баз данных
- **Просмотр структуры БД** - Изучайте таблицы, колонки, индексы и метаданные
- **Логирование запросов** - Отслеживайте все выполненные запросы с временем выполнения
- **Управление пользователями** - RBAC система с ролями (Admin, User, Viewer)
- **GraphQL API** - Гибкий и мощный API для фронтенда и интеграции
- **REST API** - Классический REST для простоты использования
- **Современный UI** - Интуитивный и красивый интерфейс
- **Redis кэширование** - Высокая производительность благодаря кэшированию
- **Docker Ready** - Легко развертывается с помощью Docker Compose

## 🏗️ Архитектура

Приложение построено на основе **Clean Architecture** с разделением на слои:

```
┌─────────────────────────────────────────┐
│   Presentation Layer (REST API, GraphQL) │
├─────────────────────────────────────────┤
│   Application Layer (Services)           │
├─────────────────────────────────────────┤
│   Domain Layer (Business Logic)          │
├─────────────────────────────────────────┤
│   Infrastructure Layer (Repositories)    │
├─────────────────────────────────────────┤
│   Data Access (ORM, PostgreSQL, Redis)   │
└─────────────────────────────────────────┘
```

## 🛠️ Стек технологий

### Backend
- **Python 3.12** - язык программирования
- **FastAPI** - асинхронный веб-фреймворк
- **SQLAlchemy 2.0** - ORM для работы с БД
- **asyncpg** - асинхронный драйвер для PostgreSQL
- **Strawberry GraphQL** - GraphQL сервер
- **Pydantic** - валидация данных
- **Passlib + bcrypt** - безопасное хеширование паролей
- **python-jose** - JWT токены

### Frontend
- **HTML5** - структура
- **CSS3** - стили (modern gradient design)
- **JavaScript (Vanilla)** - логика и взаимодействие

### DevOps
- **Docker** - контейнеризация
- **Docker Compose** - оркестрация сервисов
- **PostgreSQL 16** - основная БД
- **Redis 7** - кэширование и сессии

## 📦 Структура проекта

```
course_backend/
├── app/
│   ├── main.py                    # Точка входа приложения
│   ├── core/
│   │   ├── config.py              # Конфигурация
│   │   ├── database.py            # Подключение к БД
│   │   └── redis.py               # Подключение к Redis
│   ├── domain/
│   │   └── entities.py            # Доменные сущности
│   ├── infrastructure/
│   │   ├── models.py              # SQLAlchemy модели
│   │   └── repository.py          # Репозитории
│   ├── application/
│   │   └── services.py            # Сервисы (бизнес-логика)
│   └── presentation/
│       ├── api/
│       │   └── routers/
│       │       ├── auth.py        # Аутентификация
│       │       ├── users.py       # Управление пользователями
│       │       └── admin.py       # Администрирование
│       └── graphql/
│           └── schemas.py         # GraphQL типы
├── frontend/
│   ├── index.html                 # Главная страница
│   ├── styles.css                 # Стили
│   ├── app.js                     # Логика приложения
│   └── assets/                    # Изображения и ресурсы
├── docker-compose.yml             # Docker Compose конфиг
├── Dockerfile                     # Docker образ
├── requirements.txt               # Python зависимости
├── .env                           # Переменные окружения
└── README.md                      # Этот файл
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Git

### Установка и запуск

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository>
   cd course_backend
   ```

2. **Создайте файл .env**
   ```bash
   cp .env.example .env
   ```
   
   Содержимое .env:
   ```env
   DATABASE_URL=postgresql+asyncpg://admin:admin123@postgres:5432/db_admin
   REDIS_URL=redis://redis:6379/0
   SECRET_KEY=your-super-secret-key-change-in-production
   DEBUG=False
   ```

3. **Постройте и запустите сервисы**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

4. **Примените миграции**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

5. **Откройте приложение**
   - Фронтенд: http://localhost:8000/static/index.html
   - API документация: http://localhost:8000/docs
   - GraphQL Playground: http://localhost:8000/graphql

## 📚 API Документация

### REST API

#### Аутентификация

```bash
# Регистрация
POST /api/auth/register
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}

# Вход
POST /api/auth/login
{
  "username": "john_doe",
  "password": "secure_password"
}

# Получить текущего пользователя
GET /api/auth/me
Header: Authorization: Bearer {token}
```

#### Управление БД

```bash
# Создать подключение к БД
POST /api/admin/databases
{
  "name": "My Database",
  "host": "db.example.com",
  "port": 5432,
  "username": "admin",
  "password": "password",
  "database_name": "mydb",
  "owner_id": 1
}

# Получить список БД
GET /api/admin/databases?owner_id=1

# Получить БД по ID
GET /api/admin/databases/1

# Тестировать подключение
POST /api/admin/databases/1/test-connection

# Получить таблицы БД
GET /api/admin/databases/1/tables

# Удалить БД
DELETE /api/admin/databases/1
```

#### Управление пользователями

```bash
# Получить список пользователей
GET /api/users/

# Получить пользователя по ID
GET /api/users/1

# Обновить пользователя
PUT /api/users/1
{
  "email": "newemail@example.com",
  "full_name": "New Name"
}

# Удалить пользователя
DELETE /api/users/1
```

### GraphQL API

```graphql
# Запрос списка пользователей
query {
  listUsers(skip: 0, limit: 10) {
    id
    username
    email
    role
    isActive
  }
}

# Запрос списка БД
query {
  listDatabases(skip: 0, limit: 10) {
    id
    name
    host
    port
    status
  }
}

# Создание пользователя
mutation {
  createUser(username: "newuser", email: "user@example.com", password: "pass") {
    id
    username
    email
  }
}

# Создание подключения к БД
mutation {
  createDatabase(
    name: "My DB"
    host: "localhost"
    port: 5432
    username: "admin"
    password: "pass"
    databaseName: "mydb"
  ) {
    id
    name
    status
  }
}
```

## 🔐 Безопасность

- **Аутентификация**: JWT токены с сроком действия
- **Авторизация**: Role-Based Access Control (RBAC)
- **Хеширование**: bcrypt для пароля
- **Валидация**: Pydantic для всех входных данных
- **CORS**: Настроенный CORS для фронтенда
- **SQL Injection**: Защита через ORM SQLAlchemy

## 📊 Мониторинг и логирование

- Логирование всех действий пользователей
- Отслеживание выполненных запросов к БД
- Запись времени выполнения запросов
- Отслеживание ошибок и исключений
- Статистика использования системы

## 🧪 Тестирование

```bash
# Запустить тесты
docker-compose exec app pytest

# Запустить тесты с coverage
docker-compose exec app pytest --cov=app
```

## 📈 Производительность

### Оптимизация

- Асинхронная обработка всех операций
- Connection pooling для БД
- Redis кэширование
- Индексирование ключевых полей
- Пагинация больших списков
- Lazy loading отношений

### Масштабируемость

Приложение поддерживает масштабирование:

- **Горизонтальное**: несколько инстансов приложения за load balancer
- **Вертикальное**: увеличение ресурсов сервера
- **Кэширование**: Redis для распределенного кэша
- **Шардирование БД**: возможно при больших объемах

## 🐛 Решение проблем

### Приложение не запускается

```bash
# Проверьте логи
docker-compose logs app

# Перестройте контейнеры
docker-compose down -v
docker-compose up --build
```

### Ошибка подключения к БД

```bash
# Проверьте статус сервисов
docker-compose ps

# Проверьте переменные окружения
docker-compose exec app env | grep DATABASE
```

### Ошибки миграций

```bash
# Откатите последнюю миграцию
docker-compose exec app alembic downgrade -1

# Примените миграции заново
docker-compose exec app alembic upgrade head
```

## 📝 Документация

- [REPORT.md](./REPORT.md) - Полный отчет курсовой работы
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Архитектурные диаграммы и UML
- [API Документация](http://localhost:8000/docs) - Автоматическая документация Swagger

## 🤝 Вклад

Если вы хотите внести вклад в проект:

1. Создайте форк репозитория
2. Создайте ветку для вашей функции (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл LICENSE для деталей.

## 👨‍💻 Автор

Создано как курсовая работа по теме "Серверная часть веб-приложения «Администратор базы данных»"

## 📞 Поддержка

Если у вас есть вопросы или проблемы:

1. Проверьте раздел "Решение проблем"
2. Посмотрите логи приложения
3. Откройте Issue на GitHub

## 🎯 Планы на будущее

- [ ] Добавить поддержку MySQL и SQLite
- [ ] Реализовать резервное копирование БД
- [ ] Добавить более детальную аналитику
- [ ] Создать мобильное приложение
- [ ] Добавить поддержку множественных языков
- [ ] Реализовать кластеризацию
- [ ] Добавить биометрическую аутентификацию
- [ ] Интеграция с системами мониторинга (Prometheus, Grafana)

---

**Версия**: 1.0.0  
**Последнее обновление**: 2026-05-12  
**Статус**: Production Ready ✅
