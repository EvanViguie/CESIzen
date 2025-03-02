from typing import Optional, Dict, Any, List
from pymongo.collection import Collection
from .mongodb import users_collection
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self, collection: Collection = users_collection):
        self.collection = collection

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve a user by username from the database"""
        return self.collection.find_one({"username": username})

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve a user by email from the database"""
        return self.collection.find_one({"email": email})

    def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user in the database"""
        # Hash the password before storing
        if "password" in user_data:
            user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))
        
        # Set the default role if not provided
        if "role" not in user_data:
            user_data["role"] = "user"
            
        # Set default disabled status if not provided
        if "disabled" not in user_data:
            user_data["disabled"] = False
            
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def update_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Update an existing user in the database"""
        # Handle password updates separately to hash them
        if "password" in user_data:
            user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))
            
        result = self.collection.update_one(
            {"username": username}, 
            {"$set": user_data}
        )
        return result.modified_count > 0

    def delete_user(self, username: str) -> bool:
        """Delete a user from the database"""
        result = self.collection.delete_one({"username": username})
        return result.deleted_count > 0

    def list_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List all users with pagination"""
        return list(self.collection.find().skip(skip).limit(limit))

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_index(self):
        """Create indexes for the user's collection"""
        self.collection.create_index("username", unique=True)
        self.collection.create_index("email", unique=True)

    def init_admin_user(self, admin_username: str, admin_password: str, admin_email: str):
        """Initialize an administrator user if it doesn't exist yet"""
        if not self.get_user_by_username(admin_username):
            self.create_user({
                "username": admin_username,
                "email": admin_email,
                "password": admin_password,
                "full_name": "Admin User",
                "role": "admin",
                "disabled": False
            })
            return True
        return False