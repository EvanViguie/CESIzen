from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import uvicorn
from datetime import datetime
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import requests

# Configuration
AUTH_SERVICE_URL = "http://auth-service:8000"  # In production, use service discovery
SECRET_KEY = "YOUR_SECRET_KEY_HERE"  # Should match auth service key
ALGORITHM = "HS256"

# Models
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class User(UserBase):
    id: str
    disabled: bool = False
    created_at: datetime
    updated_at: datetime

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{AUTH_SERVICE_URL}/token")

# FastAPI app
app = FastAPI(
    title="CESIzen User Service",
    description="User management service for CESIzen application",
    version="0.1.0"
)

# Mock database - Replace with MongoDB in production
fake_users_db = {}

# Dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Verify token with auth service
        response = requests.get(
            f"{AUTH_SERVICE_URL}/verify-token",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise credentials_exception
        return response.json()
    except Exception:
        # Fallback: decode token locally (not as secure)
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            return {"username": username, "role": payload.get("role", "user")}
        except JWTError:
            raise credentials_exception

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Routes
@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    # Check if username exists
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user in auth service
    try:
        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "username": user.username,
                "password": user.password,
                "email": user.email,
                "full_name": user.full_name
            }
        )
        if auth_response.status_code != 201:
            raise HTTPException(
                status_code=auth_response.status_code,
                detail="Error creating user in auth service"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with auth service: {str(e)}"
        )
    
    # Store user in this service's database
    now = datetime.utcnow()
    user_id = str(len(fake_users_db) + 1)  # Replace with MongoDB ObjectId in production
    user_data = User(
        id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        created_at=now,
        updated_at=now
    )
    fake_users_db[user.username] = user_data
    
    return user_data

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return fake_users_db[current_user["username"]]

@app.put("/users/me", response_model=User)
async def update_user_me(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = fake_users_db[current_user["username"]]
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user_data, field, value)
    
    user_data.updated_at = datetime.utcnow()
    fake_users_db[current_user["username"]] = user_data
    
    return user_data

@app.get("/users/", response_model=List[User])
async def read_users(_: dict = Depends(get_admin_user)):
    return list(fake_users_db.values())

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)