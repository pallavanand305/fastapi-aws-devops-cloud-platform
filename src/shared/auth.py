"""
Enhanced JWT authentication utilities with proper security.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status

from .config_local import local_settings
from .logging import get_logger

logger = get_logger(__name__)


class JWTManager:
    """JWT token management with proper security."""
    
    def __init__(self):
        self.secret_key = local_settings.jwt_secret_key
        self.algorithm = local_settings.jwt_algorithm
        self.access_token_expire_minutes = local_settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = local_settings.jwt_refresh_token_expire_days
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "type": "access",
            "jti": secrets.token_urlsafe(32)  # JWT ID for token revocation
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.debug("Access token created", user_id=data.get("sub"))
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.debug("Refresh token created", user_id=data.get("sub"))
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise JWTError(f"Invalid token type. Expected {token_type}")
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise JWTError("Token has expired")
            
            return payload
            
        except JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


class PasswordManager:
    """Secure password hashing with bcrypt."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error("Password verification error", error=str(e))
            return False


class RateLimiter:
    """Simple in-memory rate limiter for authentication endpoints."""
    
    def __init__(self):
        self._attempts = {}  # {ip: [(timestamp, count), ...]}
        self.max_attempts = 5
        self.window_minutes = 15
    
    def is_rate_limited(self, identifier: str) -> bool:
        """Check if identifier is rate limited."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old attempts
        if identifier in self._attempts:
            self._attempts[identifier] = [
                (timestamp, count) for timestamp, count in self._attempts[identifier]
                if timestamp > window_start
            ]
        
        # Count attempts in current window
        total_attempts = sum(
            count for _, count in self._attempts.get(identifier, [])
        )
        
        return total_attempts >= self.max_attempts
    
    def record_attempt(self, identifier: str, failed: bool = False):
        """Record an authentication attempt."""
        now = datetime.utcnow()
        
        if identifier not in self._attempts:
            self._attempts[identifier] = []
        
        # Only record failed attempts for rate limiting
        if failed:
            self._attempts[identifier].append((now, 1))
            logger.warning("Failed authentication attempt recorded", identifier=identifier)


# Global instances
jwt_manager = JWTManager()
password_manager = PasswordManager()
rate_limiter = RateLimiter()