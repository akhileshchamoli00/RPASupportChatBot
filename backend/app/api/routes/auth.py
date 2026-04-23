from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class AuthRequest(BaseModel):
    user_id: str
    password: str

class AuthResponse(BaseModel):
    user_id: str
    message: str

# Simple mock storage for demo
mock_users = {}

@router.post("/register", response_model=AuthResponse)
def register_user(body: AuthRequest):
    if body.user_id in mock_users:
        raise HTTPException(status_code=400, detail="User already exists")
    mock_users[body.user_id] = body.password
    return AuthResponse(user_id=body.user_id, message="Registration successful")

@router.post("/login", response_model=AuthResponse)
def login_user(body: AuthRequest):
    if body.user_id not in mock_users or mock_users[body.user_id] != body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(user_id=body.user_id, message="Login successful")
