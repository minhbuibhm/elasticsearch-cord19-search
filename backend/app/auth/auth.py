from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

from app.models import LoginRequest, LoginResponse, TokenData

router = APIRouter()
security = HTTPBearer()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Simple in-memory user store (in production, use a database)
# For this demo, any username can login
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify JWT token and extract user data"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")

        if user_id is None or username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        return TokenData(user_id=user_id, username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Simple login endpoint - accepts any username
    In production, this would validate against a user database
    """
    # For demo purposes, we accept any username and create a user_id from it
    user_id = f"user_{hash(request.username) % 1000000}"

    # Create access token
    access_token = create_access_token(
        data={"user_id": user_id, "username": request.username}
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        username=request.username
    )

@router.get("/me")
async def get_current_user(token_data: TokenData = Depends(verify_token)):
    """Get current user information from token"""
    return {
        "user_id": token_data.user_id,
        "username": token_data.username
    }
