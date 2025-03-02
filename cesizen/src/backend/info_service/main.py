from fastapi import FastAPI, Depends, HTTPException, status, Body, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from typing import List, Optional
import uvicorn
from datetime import datetime

# Configuration
SECRET_KEY = "YOUR_SECRET_KEY_HERE"  # Should match auth service key
ALGORITHM = "HS256"

# Models
class ContentBase(BaseModel):
    title: str
    body: str
    category: str

class ContentCreate(ContentBase):
    pass

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None

class Content(ContentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# FastAPI app
app = FastAPI(
    title="CESIzen Information Service",
    description="Information service for CESIzen application",
    version="0.1.0"
)

# Mock database - Replace with MongoDB in production
fake_content_db = {
    "1": {
        "id": "1",
        "title": "Welcome to CESIzen",
        "body": "CESIzen is an application dedicated to stress management and mental health.",
        "category": "general",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "admin"
    },
    "2": {
        "id": "2",
        "title": "Breathing Exercises",
        "body": "Breathing exercises can help reduce stress and anxiety.",
        "category": "techniques",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "admin"
    }
}

# Dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
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
@app.get("/content/", response_model=List[Content])
async def list_content(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = 0, 
    limit: int = 10,
    _: dict = Depends(get_current_user)
):
    content_list = list(fake_content_db.values())
    
    if category:
        content_list = [c for c in content_list if c["category"] == category]
    
    return content_list[skip: skip + limit]

@app.get("/content/{content_id}", response_model=Content)
async def get_content(content_id: str, _: dict = Depends(get_current_user)):
    if content_id not in fake_content_db:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return fake_content_db[content_id]

@app.post("/content/", response_model=Content, status_code=status.HTTP_201_CREATED)
async def create_content(
    content: ContentCreate,
    current_user: dict = Depends(get_admin_user)
):
    content_id = str(len(fake_content_db) + 1)  # Replace with MongoDB ObjectId in production
    now = datetime.utcnow()
    
    content_data = Content(
        id=content_id,
        title=content.title,
        body=content.body,
        category=content.category,
        created_at=now,
        updated_at=now,
        created_by=current_user["username"]
    )
    
    fake_content_db[content_id] = content_data.dict()
    
    return content_data

@app.put("/content/{content_id}", response_model=Content)
async def update_content(
    content_id: str,
    content_update: ContentUpdate,
    _: dict = Depends(get_admin_user)
):
    if content_id not in fake_content_db:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content_data = fake_content_db[content_id]
    update_data = content_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        content_data[field] = value
    
    content_data["updated_at"] = datetime.utcnow()
    fake_content_db[content_id] = content_data
    
    return content_data

@app.delete("/content/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(content_id: str, _: dict = Depends(get_admin_user)):
    if content_id not in fake_content_db:
        raise HTTPException(status_code=404, detail="Content not found")
    
    del fake_content_db[content_id]
    
    return None

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)