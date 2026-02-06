# API Documentation

## Overview

The ML Workflow Orchestration Platform provides a RESTful API built with FastAPI. All endpoints follow REST conventions and return JSON responses.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.your-domain.com`

## Authentication

Most endpoints require authentication using JWT (JSON Web Tokens).

### Getting a Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token

Include the token in the Authorization header:

```bash
Authorization: Bearer <access_token>
```

### Refreshing Tokens

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## API Endpoints

### Health & System

#### Health Check
```bash
GET /health
```

Returns the health status of the application and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-06T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

#### Metrics
```bash
GET /metrics
```

Returns Prometheus-formatted metrics for monitoring.

### Authentication Endpoints

#### User Login
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401 Unauthorized` - Invalid credentials
- `429 Too Many Requests` - Rate limit exceeded

#### User Registration
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "full_name": "string"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "username": "string",
  "email": "user@example.com",
  "full_name": "string",
  "is_active": true,
  "created_at": "2026-02-06T10:30:00Z"
}
```

**Errors:**
- `400 Bad Request` - Validation error
- `409 Conflict` - Username or email already exists

#### Get Current User
```bash
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "username": "string",
  "email": "user@example.com",
  "full_name": "string",
  "is_active": true,
  "roles": ["user"],
  "created_at": "2026-02-06T10:30:00Z"
}
```

#### Update Profile
```bash
PUT /api/v1/auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "New Name"
}
```

**Response:** `200 OK` - Updated user object

#### Change Password
```bash
PUT /api/v1/auth/me/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "string",
  "new_password": "string"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password updated successfully"
}
```

**Errors:**
- `400 Bad Request` - Current password incorrect
- `422 Unprocessable Entity` - Password validation failed

### User Management (Admin Only)

#### Create User
```bash
POST /api/v1/auth/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "full_name": "string",
  "role_ids": ["uuid"]
}
```

**Response:** `201 Created` - User object

**Required Permission:** `admin` role

#### List Users
```bash
GET /api/v1/auth/users?skip=0&limit=100
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "username": "string",
      "email": "user@example.com",
      "full_name": "string",
      "is_active": true,
      "roles": ["user"],
      "created_at": "2026-02-06T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

#### Get User by ID
```bash
GET /api/v1/auth/users/{user_id}
Authorization: Bearer <admin_token>
```

**Response:** `200 OK` - User object

**Errors:**
- `404 Not Found` - User not found

#### Update User
```bash
PUT /api/v1/auth/users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "New Name",
  "is_active": true,
  "role_ids": ["uuid"]
}
```

**Response:** `200 OK` - Updated user object

#### Delete User
```bash
DELETE /api/v1/auth/users/{user_id}
Authorization: Bearer <admin_token>
```

**Response:** `204 No Content`

### Role Management (Admin Only)

#### Create Role
```bash
POST /api/v1/auth/roles
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "permissions": ["read:users", "write:users"]
}
```

**Response:** `201 Created` - Role object

#### List Roles
```bash
GET /api/v1/auth/roles
Authorization: Bearer <admin_token>
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "admin",
    "description": "Administrator role",
    "permissions": ["*"],
    "created_at": "2026-02-06T10:30:00Z"
  }
]
```

#### Get Role by ID
```bash
GET /api/v1/auth/roles/{role_id}
Authorization: Bearer <admin_token>
```

**Response:** `200 OK` - Role object

#### List Permissions
```bash
GET /api/v1/auth/permissions
Authorization: Bearer <admin_token>
```

**Response:** `200 OK`
```json
[
  {
    "name": "read:users",
    "description": "Read user information"
  },
  {
    "name": "write:users",
    "description": "Create and update users"
  }
]
```

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-02-06T10:30:00Z"
}
```

### Common HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `204 No Content` - Request succeeded with no response body
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Rate Limiting

Authentication endpoints are rate-limited to prevent abuse:

- **Login**: 5 requests per minute per IP
- **Registration**: 3 requests per hour per IP
- **Password Reset**: 3 requests per hour per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1675684800
```

## Pagination

List endpoints support pagination using `skip` and `limit` parameters:

```bash
GET /api/v1/auth/users?skip=20&limit=10
```

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 100,
  "skip": 20,
  "limit": 10
}
```

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Code Examples

### Python
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Get current user
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/auth/me",
    headers=headers
)
user = response.json()
```

### cURL
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get current user
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

### JavaScript (fetch)
```javascript
// Login
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { access_token } = await response.json();

// Get current user
const userResponse = await fetch('http://localhost:8000/api/v1/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const user = await userResponse.json();
```

## Webhooks (Future)

Webhook support for event notifications is planned for future releases.

## Versioning

The API uses URL versioning (e.g., `/api/v1/`). Breaking changes will result in a new version.

## Support

For API support and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [repository-url]/docs
- Email: support@your-domain.com
