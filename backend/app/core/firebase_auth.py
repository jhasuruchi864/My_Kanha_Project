"""
Firebase Authentication Helpers
- Initialize Firebase Admin
- Verify Firebase ID tokens
- Map Firebase users to local users
"""

from typing import Optional, Tuple
import firebase_admin
from firebase_admin import auth as fb_auth
from firebase_admin import credentials

from app.logger import logger
from app.core.auth_service import (
    get_user_by_username,
    update_last_login,
    create_access_token,
)

# Lazy init flag
_initialized = False


def init_firebase_admin() -> None:
    global _initialized
    if _initialized:
        return
    try:
        # Initialize with default credentials. In local dev, this works without a service account for ID token verification.
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        _initialized = True
        logger.info("Firebase Admin initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin: {e}")
        raise


def verify_firebase_id_token(id_token: str) -> Optional[dict]:
    """Verify Firebase ID token and return decoded information."""
    try:
        init_firebase_admin()
        decoded = fb_auth.verify_id_token(id_token)
        # decoded includes: uid, email, name, picture, auth_time, iss, aud, etc.
        return decoded
    except Exception as e:
        logger.warning(f"Firebase token verification failed: {e}")
        return None


def issue_server_jwt_for_user(username: str, email: str) -> Tuple[str, int]:
    """Create our server JWT for an existing user and update last login."""
    token, expires_in = create_access_token(user_id=get_user_by_username(username)["user_id"], username=username, email=email)
    update_last_login(get_user_by_username(username)["user_id"])
    return token, expires_in
