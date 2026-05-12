# Примеры запросов API

## REST API примеры

### 1. Аутентификация

#### Регистрация
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&email=admin@test.com&password=admin123&full_name=Administrator"
```

**Ответ:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@test.com"
}
```

#### Вход
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Ответ:**
```json
{
  "access_token": "token_1",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin"
}
```

#### Получить текущего пользователя
```bash
curl -X GET "http://localhost:8000/api/auth/me?user_id=1" \
  -H "Authorization: Bearer token_1"
```

### 2. Управление пользователями

#### Получить список пользователей
```bash
curl -X GET "http://localhost:8000/api/users/?skip=0&limit=10" \
  -H "Authorization: Bearer token_1"
```

**Ответ:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@test.com",
    "full_name": "Administrator",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
]
```

#### Получить пользователя по ID
```bash
curl -X GET "http://localhost:8000/api/users/1" \
  -H "Authorization: Bearer token_1"
```

#### Обновить пользователя
```bash
curl -X PUT "http://localhost:8000/api/users/1" \
  -H "Authorization: Bearer token_1" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=newemail@test.com&full_name=New Name"
```

#### Удалить пользователя
```bash
curl -X DELETE "http://localhost:8000/api/users/2" \
  -H "Authorization: Bearer token_1"
```

**Ответ:**
```json
{
  "message": "Пользователь удален"
}
```

### 3. Управление базами данных

#### Создать подключение к БД
```bash
curl -X POST "http://localhost:8000/api/admin/databases" \
  -H "Authorization: Bearer token_1" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Production&host=db.prod.com&port=5432&username=prod_user&password=prod_pass&database_name=prod_db&owner_id=1"
```

**Ответ:**
```json
{
  "id": 1,
  "name": "Production",
  "host": "db.prod.com",
  "port": 5432,
  "database_name": "prod_db",
  "status": "disconnected",
  "owner_id": 1,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

#### Получить список БД пользователя
```bash
curl -X GET "http://localhost:8000/api/admin/databases?owner_id=1&skip=0&limit=10" \
  -H "Authorization: Bearer token_1"
```

#### Получить БД по ID
```bash
curl -X GET "http://localhost:8000/api/admin/databases/1" \
  -H "Authorization: Bearer token_1"
```

#### Тестировать подключение к БД
```bash
curl -X POST "http://localhost:8000/api/admin/databases/1/test-connection" \
  -H "Authorization: Bearer token_1"
```

**Ответ при успехе:**
```json
{
  "status": "connected"
}
```

**Ответ при ошибке:**
```json
{
  "status": "error",
  "message": "Не удалось подключиться"
}
```

#### Получить таблицы БД
```bash
curl -X GET "http://localhost:8000/api/admin/databases/1/tables" \
  -H "Authorization: Bearer token_1"
```

**Ответ:**
```json
[
  {
    "name": "users"
  },
  {
    "name": "products"
  },
  {
    "name": "orders"
  }
]
```

#### Удалить БД
```bash
curl -X DELETE "http://localhost:8000/api/admin/databases/1" \
  -H "Authorization: Bearer token_1"
```

### 4. Администрирование

#### Получить статистику системы
```bash
curl -X GET "http://localhost:8000/api/admin/statistics" \
  -H "Authorization: Bearer token_1"
```

**Ответ:**
```json
{
  "total_users": 5,
  "total_databases": 12,
  "timestamp": "2024-01-01T12:30:00"
}
```

#### Получить логи запросов
```bash
curl -X GET "http://localhost:8000/api/admin/logs?database_id=1&skip=0&limit=50" \
  -H "Authorization: Bearer token_1"
```

---

## GraphQL примеры

Откройте http://localhost:8000/graphql в браузере или используйте curl:

### 1. Query примеры

#### Получить список пользователей
```graphql
query {
  listUsers(skip: 0, limit: 10) {
    id
    username
    email
    fullName
    role
    isActive
    createdAt
  }
}
```

**Ответ:**
```json
{
  "data": {
    "listUsers": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@test.com",
        "fullName": "Administrator",
        "role": "admin",
        "isActive": true,
        "createdAt": "2024-01-01T12:00:00"
      }
    ]
  }
}
```

#### Получить конкретного пользователя
```graphql
query {
  getUser(userId: 1) {
    id
    username
    email
    role
    isActive
  }
}
```

#### Получить список БД
```graphql
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
```

#### Получить конкретную БД
```graphql
query {
  getDatabase(databaseId: 1) {
    id
    name
    host
    port
    databaseName
    status
    lastChecked
  }
}
```

#### Получить таблицы БД
```graphql
query {
  getTables(databaseId: 1) {
    id
    name
    rowCount
    sizeBytes
    createdAt
  }
}
```

#### Получить логи запросов
```graphql
query {
  getQueryLogs(databaseId: 1, limit: 50) {
    id
    queryText
    status
    errorMessage
    executionTimeMs
    createdAt
  }
}
```

#### Hello запрос (проверка соединения)
```graphql
query {
  hello(name: "World")
}
```

**Ответ:**
```json
{
  "data": {
    "hello": "Hello, World!"
  }
}
```

### 2. Mutation примеры

#### Создать пользователя
```graphql
mutation {
  createUser(
    username: "john_doe"
    email: "john@example.com"
    password: "secure_password"
  ) {
    id
    username
    email
    createdAt
  }
}
```

#### Создать подключение к БД
```graphql
mutation {
  createDatabase(
    name: "My Production DB"
    host: "db.example.com"
    port: 5432
    username: "prod_user"
    password: "prod_password"
    databaseName: "production"
  ) {
    id
    name
    host
    status
    createdAt
  }
}
```

#### Тестировать подключение
```graphql
mutation {
  testDatabaseConnection(
    host: "localhost"
    port: 5432
    username: "admin"
    password: "admin123"
    databaseName: "test_db"
  )
}
```

**Ответ:**
```json
{
  "data": {
    "testDatabaseConnection": true
  }
}
```

#### Удалить БД
```graphql
mutation {
  deleteDatabase(databaseId: 1)
}
```

**Ответ:**
```json
{
  "data": {
    "deleteDatabase": true
  }
}
```

---

## Примеры с curl для GraphQL

### Получить список пользователей (POST запрос)

```bash
curl -X POST "http://localhost:8000/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { listUsers(skip: 0, limit: 10) { id username email role } }"
  }'
```

### Создать пользователя (POST запрос)

```bash
curl -X POST "http://localhost:8000/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { createUser(username: \"test\", email: \"test@test.com\", password: \"test123\") { id username } }"
  }'
```

### С переменными

```bash
curl -X POST "http://localhost:8000/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query getUser($id: Int!) { getUser(userId: $id) { id username email } }",
    "variables": {
      "id": 1
    }
  }'
```

---

## Примеры для JavaScript (Fetch API)

### REST API

```javascript
// Регистрация
async function register() {
  const response = await fetch('http://localhost:8000/api/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: 'username=admin&email=admin@test.com&password=admin123&full_name=Admin'
  });
  const data = await response.json();
  console.log(data);
}

// Вход
async function login() {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: 'username=admin&password=admin123'
  });
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
}

// Получить список пользователей
async function getUsers(token) {
  const response = await fetch('http://localhost:8000/api/users/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}
```

### GraphQL

```javascript
// GraphQL запрос
async function graphqlQuery(query, variables = {}) {
  const response = await fetch('http://localhost:8000/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query,
      variables
    })
  });
  return await response.json();
}

// Использование
async function listUsers() {
  const query = `
    query {
      listUsers(skip: 0, limit: 10) {
        id
        username
        email
      }
    }
  `;
  const result = await graphqlQuery(query);
  console.log(result.data.listUsers);
}

async function createDatabase(name, host, port) {
  const query = `
    mutation createDatabase($name: String!, $host: String!, $port: Int!) {
      createDatabase(
        name: $name
        host: $host
        port: $port
        username: "admin"
        password: "admin"
        databaseName: "test"
      ) {
        id
        name
        status
      }
    }
  `;
  const result = await graphqlQuery(query, { name, host, port });
  console.log(result.data.createDatabase);
}
```

---

## Примеры для Python (requests)

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Регистрация
def register():
    response = requests.post(f"{BASE_URL}/api/auth/register", data={
        "username": "admin",
        "email": "admin@test.com",
        "password": "admin123",
        "full_name": "Administrator"
    })
    return response.json()

# Вход
def login():
    response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    return response.json()

# Получить список БД
def get_databases(token, user_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/admin/databases",
        headers=headers,
        params={"owner_id": user_id}
    )
    return response.json()

# GraphQL запрос
def graphql_query(query, variables=None):
    headers = {"Content-Type": "application/json"}
    data = {
        "query": query,
        "variables": variables or {}
    }
    response = requests.post(f"{BASE_URL}/graphql", json=data, headers=headers)
    return response.json()

# Получить пользователей через GraphQL
def get_users_graphql():
    query = """
    query {
        listUsers(skip: 0, limit: 10) {
            id
            username
            email
            role
        }
    }
    """
    return graphql_query(query)

if __name__ == "__main__":
    # Регистрация
    user = register()
    print("Registered:", user)
    
    # Вход
    login_data = login()
    token = login_data['access_token']
    user_id = login_data['user_id']
    print("Token:", token)
    
    # Получить БД
    databases = get_databases(token, user_id)
    print("Databases:", databases)
    
    # GraphQL запрос
    users = get_users_graphql()
    print("Users (GraphQL):", users)
```

---

## Полезные Tips

1. **Сохраняйте токен** после входа - используйте его для последующих запросов
2. **Используйте GraphQL для сложных запросов** - запрашивайте только нужные поля
3. **Проверяйте ошибки** в ответах API - они содержат информацию о проблеме
4. **Используйте curl для тестирования** - быстро проверить API
5. **Используйте Swagger UI** (http://localhost:8000/docs) для интерактивного тестирования
6. **Логируйте успешные запросы** - помогает при дебагинге
