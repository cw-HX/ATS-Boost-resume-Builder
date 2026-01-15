"""
Authentication dependencies for FastAPI.
"""
from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.core.security import decode_token, validate_token_type
from app.core.database import get_users_collection
from app.models.schemas import UserResponse

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """
    Dependency to get the current authenticated user.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        UserResponse object for the authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Validate token type
    if not validate_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Fetch user from database
    users_collection = get_users_collection()
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    if user is None:
        raise credentials_exception
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        created_at=user["created_at"],
        last_login=user.get("last_login")
    )


async def get_current_user_id(
    current_user: UserResponse = Depends(get_current_user)
) -> str:
    """
    Dependency to get just the current user's ID.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User ID string
    """
    return current_user.id


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify a refresh token and return the user ID.
    
    Args:
        token: Refresh token string
        
    Returns:
        User ID if valid, None otherwise
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if not validate_token_type(payload, "refresh"):
        return None
    
    return payload.get("sub")
