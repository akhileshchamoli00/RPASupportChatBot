from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.postgres_database.database import get_db
from app.postgres_database import crud

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class AuthRequest(BaseModel):
    user_id: str
    password: str

class AuthResponse(BaseModel):
    user_id: str
    message: str

@router.post("/register", response_model=AuthResponse)
def register_user(body: AuthRequest, db: Session = Depends(get_db)):
    username = body.user_id.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not body.password or len(body.password) < 3:
        raise HTTPException(status_code=400, detail="Password must be at least 3 characters")
    
    existing = crud.get_user_by_username(db, username)
    if existing:
        raise HTTPException(status_code=400, detail="Username is already taken")

    crud.create_user(db, username=username, password=body.password)
    return AuthResponse(user_id=username, message="Registration successful")

@router.post("/login", response_model=AuthResponse)
def login_user(body: AuthRequest, db: Session = Depends(get_db)):
    username = body.user_id.strip().lower()
    user = crud.get_user_by_username(db, username)
    if not user or not crud.verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return AuthResponse(user_id=user.username, message="Login successful")
