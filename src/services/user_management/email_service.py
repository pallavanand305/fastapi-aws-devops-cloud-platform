"""
Email service for user management operations.

This module provides email functionality for:
- Email verification
- Password reset
- Account notifications
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from src.shared.logging import get_logger
from src.shared.config_local import local_settings

logger = get_logger(__name__)


class EmailVerificationService:
    """Service for managing email verification tokens and sending verification emails."""
    
    # In-memory storage for verification tokens (in production, use Redis or database)
    _verification_tokens: dict[str, dict] = {}
    
    @classmethod
    def generate_verification_token(cls, user_id: str, email: str) -> str:
        """
        Generate a verification token for a user.
        
        Args:
            user_id: User ID
            email: User email address
            
        Returns:
            Verification token string
        """
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=24)
        
        cls._verification_tokens[token] = {
            "user_id": user_id,
            "email": email,
            "expiry": expiry,
            "used": False
        }
        
        logger.info("Verification token generated", user_id=user_id, email=email)
        return token
    
    @classmethod
    def verify_token(cls, token: str) -> Optional[dict]:
        """
        Verify a verification token.
        
        Args:
            token: Verification token
            
        Returns:
            Token data if valid, None otherwise
        """
        token_data = cls._verification_tokens.get(token)
        
        if not token_data:
            logger.warning("Invalid verification token", token=token[:10])
            return None
        
        if token_data["used"]:
            logger.warning("Verification token already used", token=token[:10])
            return None
        
        if datetime.utcnow() > token_data["expiry"]:
            logger.warning("Verification token expired", token=token[:10])
            return None
        
        return token_data
    
    @classmethod
    def mark_token_used(cls, token: str) -> bool:
        """
        Mark a verification token as used.
        
        Args:
            token: Verification token
            
        Returns:
            True if successful, False otherwise
        """
        if token in cls._verification_tokens:
            cls._verification_tokens[token]["used"] = True
            logger.info("Verification token marked as used", token=token[:10])
            return True
        return False
    
    @classmethod
    def send_verification_email(cls, email: str, token: str) -> bool:
        """
        Send verification email to user.
        
        In production, this would integrate with an email service like SendGrid, SES, etc.
        For now, we log the verification link.
        
        Args:
            email: User email address
            token: Verification token
            
        Returns:
            True if email sent successfully
        """
        verification_url = f"{local_settings.app_url}/api/v1/auth/verify-email?token={token}"
        
        # In production, send actual email
        # For development, log the verification link
        logger.info(
            "Email verification link generated",
            email=email,
            verification_url=verification_url
        )
        
        # TODO: Integrate with email service provider
        # Example: send_email(to=email, subject="Verify your email", body=f"Click here: {verification_url}")
        
        return True
    
    @classmethod
    def resend_verification_email(cls, user_id: str, email: str) -> str:
        """
        Resend verification email to user.
        
        Args:
            user_id: User ID
            email: User email address
            
        Returns:
            New verification token
        """
        # Invalidate old tokens for this user
        for token, data in list(cls._verification_tokens.items()):
            if data["user_id"] == user_id and not data["used"]:
                data["used"] = True
        
        # Generate new token
        token = cls.generate_verification_token(user_id, email)
        cls.send_verification_email(email, token)
        
        return token


class PasswordResetService:
    """Service for managing password reset tokens."""
    
    # In-memory storage for reset tokens (in production, use Redis or database)
    _reset_tokens: dict[str, dict] = {}
    
    @classmethod
    def generate_reset_token(cls, user_id: str, email: str) -> str:
        """
        Generate a password reset token.
        
        Args:
            user_id: User ID
            email: User email address
            
        Returns:
            Reset token string
        """
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=1)  # Shorter expiry for security
        
        cls._reset_tokens[token] = {
            "user_id": user_id,
            "email": email,
            "expiry": expiry,
            "used": False
        }
        
        logger.info("Password reset token generated", user_id=user_id, email=email)
        return token
    
    @classmethod
    def verify_reset_token(cls, token: str) -> Optional[dict]:
        """
        Verify a password reset token.
        
        Args:
            token: Reset token
            
        Returns:
            Token data if valid, None otherwise
        """
        token_data = cls._reset_tokens.get(token)
        
        if not token_data:
            logger.warning("Invalid reset token", token=token[:10])
            return None
        
        if token_data["used"]:
            logger.warning("Reset token already used", token=token[:10])
            return None
        
        if datetime.utcnow() > token_data["expiry"]:
            logger.warning("Reset token expired", token=token[:10])
            return None
        
        return token_data
    
    @classmethod
    def mark_reset_token_used(cls, token: str) -> bool:
        """
        Mark a reset token as used.
        
        Args:
            token: Reset token
            
        Returns:
            True if successful, False otherwise
        """
        if token in cls._reset_tokens:
            cls._reset_tokens[token]["used"] = True
            logger.info("Reset token marked as used", token=token[:10])
            return True
        return False
    
    @classmethod
    def send_reset_email(cls, email: str, token: str) -> bool:
        """
        Send password reset email to user.
        
        Args:
            email: User email address
            token: Reset token
            
        Returns:
            True if email sent successfully
        """
        reset_url = f"{local_settings.app_url}/api/v1/auth/reset-password?token={token}"
        
        # In production, send actual email
        logger.info(
            "Password reset link generated",
            email=email,
            reset_url=reset_url
        )
        
        # TODO: Integrate with email service provider
        
        return True
