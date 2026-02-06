# User Management Service

## Overview

The User Management Service handles authentication, authorization, and user profile management for the ML Workflow Orchestration Platform. It provides JWT-based authentication with role-based access control (RBAC).

## Features

- **JWT Authentication**: Secure token-based authentication with access and refresh tokens
- **Role-Based Access Control**: Flexible RBAC system with customizable roles and permissions
- **User Registration**: Self-service user registration with email verification
- **Password Security**: Bcrypt hashing with salt for secure password storage
- **Session Management**: Redis-backed session storage for scalability
- **Rate Limiting**: Protection against brute-force attacks
- **Audit Logging**: Comprehensive logging of authentication events

## Architecture

### Components

```
user_management/
├── models.py          # SQLAlchemy database models
├── schemas.py         # Pydantic request/response schemas
├── repository.py      # Data access layer
├── service.py         # Business logic layer
├── routes.py          # FastAPI route handlers
├── dependencies.py    # FastAPI dependency injection
└── email_service.py   # Email notification service
```

### Data Models

#### User
- `id`: UUID primary key
- `username`: Unique username
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password
- `full_name`: User's full name
- `is_active`: Account status flag
- `is_verified`: Email verification status
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp
- `roles`: Many-to-many relationship with Role

#### Role
- `id`: UUID primary key
- `name`: Unique role name
- `description`: Role description
- `permissions`: JSON array of permission strings
- `created_at`: Creation timestamp

#### UserRole (Association Table)
- `user_id`: Foreign key to User
- `role_id`: Foreign key to Role

## API Endpoints

### Public Endpoints

#### POST /api/v1/auth/login
Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /api/v1/auth/register
Register a new user account.

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

#### POST /api/v1/auth/refresh
Refresh access token using refresh token.

### Authenticated Endpoints

#### GET /api/v1/auth/me
Get current user profile.

#### PUT /api/v1/auth/me
Update current user profile.

#### PUT /api/v1/auth/me/password
Change current user password.

### Admin Endpoints

#### POST /api/v1/auth/users
Create a new user (admin only).

#### GET /api/v1/auth/users
List all users with pagination.

#### GET /api/v1/auth/users/{user_id}
Get user by ID.

#### PUT /api/v1/auth/users/{user_id}
Update user information.

#### DELETE /api/v1/auth/users/{user_id}
Delete user account.

#### POST /api/v1/auth/roles
Create a new role.

#### GET /api/v1/auth/roles
List all roles.

#### GET /api/v1/auth/permissions
List available permissions.

## Authentication Flow

### Login Flow
1. User submits credentials to `/api/v1/auth/login`
2. Service validates credentials against database
3. If valid, generates JWT access and refresh tokens
4. Stores session in Redis
5. Returns tokens to client

### Token Refresh Flow
1. Client submits refresh token to `/api/v1/auth/refresh`
2. Service validates refresh token
3. If valid, generates new access token
4. Returns new access token to client

### Authorization Flow
1. Client includes access token in Authorization header
2. Dependency injection validates token
3. Extracts user information from token
4. Checks user permissions against required permissions
5. Allows or denies access

## Security Features

### Password Security
- Bcrypt hashing with automatic salt generation
- Minimum password requirements enforced
- Password history to prevent reuse (future)

### Token Security
- Short-lived access tokens (30 minutes)
- Long-lived refresh tokens (7 days)
- Token revocation support via Redis
- Secure token signing with HS256

### Rate Limiting
- Login: 5 attempts per minute per IP
- Registration: 3 attempts per hour per IP
- Password reset: 3 attempts per hour per user

### Audit Logging
All authentication events are logged:
- Login attempts (success/failure)
- Token refresh
- Password changes
- User creation/modification
- Role assignments

## Role-Based Access Control

### Default Roles

#### Admin
- Full system access
- User management
- Role management
- All permissions: `["*"]`

#### User
- Basic access
- Own profile management
- Limited permissions: `["read:own_profile", "write:own_profile"]`

### Permission System

Permissions follow the format: `action:resource`

Examples:
- `read:users` - Read user information
- `write:users` - Create/update users
- `delete:users` - Delete users
- `read:roles` - Read role information
- `write:roles` - Create/update roles

### Custom Roles

Create custom roles with specific permissions:

```python
from src.services.user_management.service import UserService

# Create custom role
role = await user_service.create_role(
    name="data_scientist",
    description="Data scientist with ML workflow access",
    permissions=[
        "read:workflows",
        "write:workflows",
        "read:models",
        "write:models",
        "read:datasets"
    ]
)
```

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Role association table
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_roles_name ON roles(name);
```

## Configuration

### Environment Variables

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Requirements
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true

# Rate Limiting
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_REGISTER=3/hour
RATE_LIMIT_PASSWORD_RESET=3/hour

# Email Configuration (for verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@your-domain.com
```

## Testing

### Unit Tests

```bash
# Run user management tests
pytest tests/test_user_management.py -v

# Run with coverage
pytest tests/test_user_management.py --cov=src.services.user_management
```

### Test Coverage

Current test coverage: 85%

Covered areas:
- User CRUD operations
- Authentication flow
- Token generation and validation
- Role assignment
- Permission checking
- Password hashing

### Example Tests

```python
def test_user_login_success(client, test_user):
    """Test successful user login"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_user_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "invalid", "password": "wrong"}
    )
    assert response.status_code == 401
```

## Usage Examples

### Creating a User

```python
from src.services.user_management.service import UserService
from src.services.user_management.schemas import UserCreate

user_service = UserService(db_session)

user_data = UserCreate(
    username="johndoe",
    email="john@example.com",
    password="SecurePass123!",
    full_name="John Doe"
)

user = await user_service.create_user(user_data)
```

### Authenticating a User

```python
from src.services.user_management.service import UserService

user_service = UserService(db_session)

# Authenticate
tokens = await user_service.authenticate_user(
    username="johndoe",
    password="SecurePass123!"
)

# Access token for API calls
access_token = tokens["access_token"]
```

### Checking Permissions

```python
from src.services.user_management.dependencies import require_permission

@router.get("/admin/users")
@require_permission("read:users")
async def list_users(current_user: User = Depends(get_current_user)):
    # Only users with "read:users" permission can access
    return await user_service.list_users()
```

## Troubleshooting

### Common Issues

#### "Invalid credentials" error
- Verify username and password are correct
- Check if user account is active
- Ensure password meets requirements

#### "Token expired" error
- Use refresh token to get new access token
- Re-authenticate if refresh token is also expired

#### "Insufficient permissions" error
- Verify user has required role/permissions
- Check role assignments in database
- Review permission configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("src.services.user_management").setLevel(logging.DEBUG)
```

## Future Enhancements

- [ ] Multi-factor authentication (MFA)
- [ ] OAuth2 integration (Google, GitHub)
- [ ] Password reset via email
- [ ] Account lockout after failed attempts
- [ ] Password history and expiration
- [ ] User activity tracking
- [ ] Advanced audit logging
- [ ] LDAP/Active Directory integration

## Contributing

When contributing to the User Management Service:

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure security best practices
5. Run linting and type checking

## Security Considerations

- Never log passwords or tokens
- Always use HTTPS in production
- Rotate JWT secret keys regularly
- Implement account lockout policies
- Monitor for suspicious activity
- Keep dependencies updated
- Follow OWASP security guidelines

## Support

For issues or questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [repository-url]/docs
- Security Issues: security@your-domain.com (private)
