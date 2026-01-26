"""
Authentication Routes
Register, login, and token refresh endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Header
from typing import Optional

from app.models.user_models import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
)
from app.core.auth_service import (
    init_db,
    create_user,
    get_user_by_username,
    get_user_by_email,
    verify_password,
    verify_token,
    create_access_token,
    update_last_login,
    create_or_link_firebase_user,
)
from app.logger import logger
from app.core.firebase_auth import verify_firebase_id_token

# Initialize database on import
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to initialize auth database: {e}")

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to get current authenticated user from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    
    token = parts[1]
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister) -> dict:
    """
    Register a new user account.
    
    Returns access token and user info.
    """
    try:
        # Create user
        user = create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        # Generate token
        token, expires_in = create_access_token(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"]
        )
        
        # Update last login
        update_last_login(user["user_id"])
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user),
            expires_in=expires_in
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin) -> dict:
    """
    Login with username/email and password.
    
    Returns access token and user info.
    """
    try:
        # Get user
        user = get_user_by_username(credentials.username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Generate token
        token, expires_in = create_access_token(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"]
        )
        
        # Update last login
        update_last_login(user["user_id"])
        
        # Remove password_hash from response
        user_info = {k: v for k, v in user.items() if k != "password_hash"}
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user_info),
            expires_in=expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(token_data = Depends(get_current_user)) -> dict:
    """
    Get current authenticated user's profile.
    """
    try:
        user = get_user_by_username(token_data.username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Remove password_hash from response
        user_info = {k: v for k, v in user.items() if k != "password_hash"}
        
        return UserResponse(**user_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data = Depends(get_current_user)):
    """
    Refresh access token.
    """
    try:
        # Generate new token
        token, expires_in = create_access_token(
            user_id=token_data.user_id,
            username=token_data.username,
            email=token_data.email
        )
        
        user = get_user_by_username(token_data.username)
        user_info = {k: v for k, v in user.items() if k != "password_hash"}
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user_info),
            expires_in=expires_in
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/firebase", response_model=TokenResponse)
async def firebase_login(payload: dict):
    """
    Login via Firebase ID token.

    Body: { id_token: string }
    """
    try:
        id_token = payload.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="Missing id_token")

        decoded = verify_firebase_id_token(id_token)
        if not decoded:
            raise HTTPException(status_code=401, detail="Invalid Firebase token")

        uid = decoded.get("uid")
        email = decoded.get("email")
        name = decoded.get("name")

        if not email:
            raise HTTPException(status_code=400, detail="Firebase token missing email")

        # Link or create local user
        user = create_or_link_firebase_user(uid=uid, email=email, name=name)

        # Generate server JWT
        token, expires_in = create_access_token(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"]
        )
        update_last_login(user["user_id"])

        user_info = {k: v for k, v in user.items() if k != "password_hash"}

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user_info),
            expires_in=expires_in
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Firebase login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")
