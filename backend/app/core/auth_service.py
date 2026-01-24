"""
Authentication Service
JWT token generation, validation, and user management.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from pathlib import Path

from app.logger import logger
from app.models.user_models import TokenData


# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production-secret-key-12345")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Database path
DB_DIR = Path("./data/users")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "users.db"


def init_db():
    """Initialize SQLite database for users."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                language TEXT DEFAULT 'english',
                sources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                INDEX idx_user_id (user_id),
                INDEX idx_session_id (session_id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def hash_password(password: str) -> str:
    """Hash password with salt."""
    salt = secrets.token_hex(32)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${pwd_hash.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        salt, pwd_hash = password_hash.split("$")
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return new_hash.hex() == pwd_hash
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_user(username: str, email: str, password: str, full_name: Optional[str] = None) -> dict:
    """Create a new user."""
    try:
        user_id = secrets.token_hex(16)
        password_hash = hash_password(password)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (user_id, username, email, full_name, password_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, email, full_name, password_hash))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User created: {username}")
        return {
            "user_id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "created_at": datetime.now()
        }
    except sqlite3.IntegrityError as e:
        logger.error(f"User creation failed: {e}")
        if "username" in str(e):
            raise ValueError("Username already exists")
        elif "email" in str(e):
            raise ValueError("Email already exists")
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise


def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, email, full_name, password_hash, created_at, last_login
            FROM users
            WHERE (username = ? OR email = ?) AND is_active = 1
        """, (username, username))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return None


def update_last_login(user_id: str) -> None:
    """Update user's last login timestamp."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating last login: {e}")


def create_access_token(user_id: str, username: str, email: str) -> tuple[str, int]:
    """Create JWT access token."""
    try:
        expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        payload = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "exp": expiration,
            "iat": datetime.utcnow()
        }
        
        token = encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        expires_in = int((expiration - datetime.utcnow()).total_seconds())
        
        return token, expires_in
    except Exception as e:
        logger.error(f"Error creating token: {e}")
        raise


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode JWT token."""
    try:
        payload = decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        user_id = payload.get("user_id")
        username = payload.get("username")
        email = payload.get("email")
        
        if not all([user_id, username, email]):
            return None
        
        return TokenData(user_id=user_id, username=username, email=email)
    except ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None
