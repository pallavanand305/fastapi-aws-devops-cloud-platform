"""
Redis session management for user authentication.
"""
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .config_local import local_settings
from .logging import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Session management with Redis backend (fallback to in-memory)."""
    
    def __init__(self):
        self.redis_client = None
        self._memory_sessions = {}  # Fallback for local development
        
        if REDIS_AVAILABLE:
            try:
                # Try to connect to Redis
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=1,
                    socket_timeout=1
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis session store connected")
            except Exception as e:
                logger.warning("Redis not available, using in-memory sessions", error=str(e))
                self.redis_client = None
        else:
            logger.warning("Redis not installed, using in-memory sessions")
    
    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session."""
        return f"session:{session_id}"
    
    async def create_session(self, user_id: str, user_data: Dict[str, Any]) -> str:
        """Create a new user session."""
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat()
        }
        
        if self.redis_client:
            try:
                # Store in Redis with expiration
                key = self._get_session_key(session_id)
                self.redis_client.setex(
                    key,
                    timedelta(days=local_settings.jwt_refresh_token_expire_days),
                    json.dumps(session_data)
                )
                logger.debug("Session created in Redis", session_id=session_id, user_id=user_id)
            except Exception as e:
                logger.error("Failed to create Redis session", error=str(e))
                # Fallback to memory
                self._memory_sessions[session_id] = session_data
        else:
            # Store in memory
            self._memory_sessions[session_id] = session_data
            logger.debug("Session created in memory", session_id=session_id, user_id=user_id)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        if self.redis_client:
            try:
                key = self._get_session_key(session_id)
                session_data = self.redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    # Update last accessed time
                    data["last_accessed"] = datetime.utcnow().isoformat()
                    self.redis_client.setex(
                        key,
                        timedelta(days=local_settings.jwt_refresh_token_expire_days),
                        json.dumps(data)
                    )
                    return data
            except Exception as e:
                logger.error("Failed to get Redis session", error=str(e))
                # Try memory fallback
                return self._memory_sessions.get(session_id)
        else:
            # Get from memory
            session_data = self._memory_sessions.get(session_id)
            if session_data:
                session_data["last_accessed"] = datetime.utcnow().isoformat()
            return session_data
        
        return None
    
    async def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """Update session data."""
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
        
        session_data["user_data"] = user_data
        session_data["last_accessed"] = datetime.utcnow().isoformat()
        
        if self.redis_client:
            try:
                key = self._get_session_key(session_id)
                self.redis_client.setex(
                    key,
                    timedelta(days=local_settings.jwt_refresh_token_expire_days),
                    json.dumps(session_data)
                )
                return True
            except Exception as e:
                logger.error("Failed to update Redis session", error=str(e))
                # Fallback to memory
                self._memory_sessions[session_id] = session_data
                return True
        else:
            # Update in memory
            self._memory_sessions[session_id] = session_data
            return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        if self.redis_client:
            try:
                key = self._get_session_key(session_id)
                result = self.redis_client.delete(key)
                logger.debug("Session deleted from Redis", session_id=session_id)
                return bool(result)
            except Exception as e:
                logger.error("Failed to delete Redis session", error=str(e))
                # Try memory fallback
                if session_id in self._memory_sessions:
                    del self._memory_sessions[session_id]
                    return True
        else:
            # Delete from memory
            if session_id in self._memory_sessions:
                del self._memory_sessions[session_id]
                logger.debug("Session deleted from memory", session_id=session_id)
                return True
        
        return False
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (for memory storage)."""
        if not self.redis_client:
            # Redis handles expiration automatically
            # Only need to clean memory sessions
            now = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session_data in self._memory_sessions.items():
                created_at = datetime.fromisoformat(session_data["created_at"])
                if now - created_at > timedelta(days=local_settings.jwt_refresh_token_expire_days):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self._memory_sessions[session_id]
                logger.debug("Expired session cleaned up", session_id=session_id)


# Global session manager instance
session_manager = SessionManager()