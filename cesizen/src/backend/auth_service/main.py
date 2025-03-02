from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn
import os
from database.user_repository import UserRepository
from database.mongodb import mongo_db

# Configuration - Use environment variables in production
SECRET_KEY = os.environ.get("SECRET_KEY", "YOUR_SECRET_KEY_HERE")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")

# Initialize user repository
user_repository = UserRepository()


# Models
class Token(BaseModel):
    """Represents an authorization token for authentication purposes."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Represents data extracted from a token."""
    username: Optional[str] = None
    role: Optional[str] = None


class UserBase(BaseModel):
    """Base user model with common attributes."""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False
    role: str = "user"  # Default role


class UserCreate(UserBase):
    """User creation model with password."""
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "johndoe@example.com",
                "full_name": "John Doe",
                "password": "securepassword",
                "role": "user"
            }
        }


class UserUpdate(BaseModel):
    """User update model with optional fields."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    disabled: Optional[bool] = None
    role: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "newemail@example.com",
                "full_name": "Updated Name"
            }
        }


class User(UserBase):
    """User response model."""
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "johndoe@example.com",
                "full_name": "John Doe",
                "disabled": False,
                "role": "user"
            }
        }


class UserInDB(UserBase):
    """User model as stored in the database."""
    hashed_password: str


# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(username: str):
    """
    Fetches a user from the MongoDB by their username.
    
    Args:
        username: The username of the user to retrieve.
        
    Returns:
        UserInDB object if the username exists, otherwise None.
    """
    user_data = user_repository.get_user_by_username(username)
    if user_data:
        return UserInDB(**user_data)
    return None


def authenticate_user(username: str, password: str):
    """
    Authenticates a user by verifying username and password.
    
    Args:
        username: Username to identify the user
        password: Password provided by the user
        
    Returns:
        User object if authentication is successful, otherwise False
    """
    user = get_user(username)
    if not user:
        return False
    if not user_repository.verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Generate a JSON Web Token (JWT) with an expiration time to grant secure access.

    This function creates an encoded JWT for the given payload and an optional
    expiration delta. If no expiration delta is provided, a default expiration time
    of 15 minutes is used.

    :param data: The payload to encode in the JWT. It should be passed as a
        dictionary containing key-value pairs representing the data to
        include in the JWT.
    :param expires_delta: Optional timedelta to specify the expiration duration
        for the token. If provided, the token expires after the given duration.
        If absent, a default expiration time of 15 minutes is applied.
    :return: Encoded JWT as a string containing the payload along with
        the expiration timestamp.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user based on JWT token.
    
    Args:
        token: JWT token from authorization header
        
    Returns:
        User object for the authenticated user
        
    Raises:
        HTTPException: If token is invalid or user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "user")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    """
    Get the current active (non-disabled) user.
    
    Args:
        current_user: User object from get_current_user dependency
        
    Returns:
        User object if active
        
    Raises:
        HTTPException: If user is disabled
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(current_user: UserInDB = Depends(get_current_user)):
    """
    Get the current user if they have admin privileges.
    
    Args:
        current_user: User object from get_current_user dependency
        
    Returns:
        User object if admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# FastAPI app
app = FastAPI(
    title="CESIzen Auth Service",
    description="Authentication service for CESIzen application",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize DB
@app.on_event("startup")
async def startup_db_client():
    # Create indexes
    user_repository.create_index()
    
    # Initialize admin user if it doesn't exist
    user_repository.init_admin_user(
        admin_username=ADMIN_USERNAME,
        admin_password=ADMIN_PASSWORD,
        admin_email=ADMIN_EMAIL
    )

# Shutdown event to close DB connection
@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_db.close()

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# User management endpoints
@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    Create a new user.
    """
    # Check if username already exists
    existing_user = user_repository.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if user.email:
        existing_email = user_repository.get_user_by_email(user.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user
    user_data = user.dict()
    user_repository.create_user(user_data)
    
    # Return user data without password
    return {k: v for k, v in user_data.items() if k != "password"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user information.
    """
    return current_user

@app.put("/users/me/", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update current user information.
    """
    # Filter out None values
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    
    if update_data:
        # Check if email is being changed and already exists
        if "email" in update_data and update_data["email"] != current_user.email:
            existing_email = user_repository.get_user_by_email(update_data["email"])
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user
        success = user_repository.update_user(current_user.username, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    # Return updated user
    updated_user = get_user(current_user.username)
    return updated_user

# Admin endpoints
@app.get("/admin/users/", response_model=List[User])
async def list_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: UserInDB = Depends(get_admin_user)
):
    """
    List all users. Admin only.
    """
    users = user_repository.list_users(skip=skip, limit=limit)
    return users

@app.get("/admin/users/{username}", response_model=User)
async def get_user_by_username(
    username: str,
    current_user: UserInDB = Depends(get_admin_user)
):
    """
    Get a specific user by username. Admin only.
    """
    user_data = user_repository.get_user_by_username(username)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user_data

@app.put("/admin/users/{username}", response_model=User)
async def admin_update_user(
    username: str,
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_admin_user)
):
    """
    Update a specific user by username. Admin only.
    """
    # Check if user exists
    user_data = user_repository.get_user_by_username(username)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Filter out None values
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    
    if update_data:
        # Check if email is being changed and already exists
        if "email" in update_data and update_data["email"] != user_data["email"]:
            existing_email = user_repository.get_user_by_email(update_data["email"])
            if existing_email and existing_email["username"] != username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user
        success = user_repository.update_user(username, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    # Return updated user
    updated_user = get_user(username)
    return updated_user

@app.delete("/admin/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    username: str,
    current_user: UserInDB = Depends(get_admin_user)
):
    """
    Delete a user. Admin only.
    """
    # Prevent deleting own account
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete user
    success = user_repository.delete_user(username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    try:
        # Verify database connection
        mongo_db.client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
