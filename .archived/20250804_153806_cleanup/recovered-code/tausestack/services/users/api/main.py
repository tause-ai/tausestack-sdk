"""
Users service API.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os

app = FastAPI(
    title="Users Service",
    description="TauseStack Users Management Service",
    version="0.7.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

# In-memory storage for demo
users_db = {}
user_id_counter = 1

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Users Service", "version": "0.7.0"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "users"}

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user."""
    global user_id_counter
    
    # Check if email already exists
    for existing_user in users_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = {
        "id": user_id_counter,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": True,
        "is_verified": False
    }
    
    users_db[user_id_counter] = new_user
    user_id_counter += 1
    
    return UserResponse(**new_user)

@app.get("/users", response_model=List[UserResponse])
async def list_users():
    """List all users."""
    return [UserResponse(**user) for user in users_db.values()]

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get a specific user by ID."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**users_db[user_id])

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate):
    """Update a user."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    # Update fields
    if user_update.username is not None:
        user["username"] = user_update.username
    if user_update.full_name is not None:
        user["full_name"] = user_update.full_name
    if user_update.is_active is not None:
        user["is_active"] = user_update.is_active
    
    return UserResponse(**user)

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    del users_db[user_id]
    return {"message": "User deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 