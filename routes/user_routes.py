from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from models.user_model import UserCreate, UserLogin, UserOut
from core.mongo import users_collection
from core.auth import get_current_user, admin_required, verify_recaptcha
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

user_router = APIRouter()

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # Default to 1 hour


# Helper: hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Helper: verify password
def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)

# Helper: create token
def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=2)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# POST /signup
@user_router.post("/signup", status_code=201)
async def signup(user: UserCreate):
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")

    user_dict = user.dict()
    user_dict["hashed_password"] = hash_password(user.password)
    user_dict.pop("password")
    user_dict["role"] = "admin" if await users_collection.count_documents({}) == 0 else "user"
    user_dict["created_at"] = datetime.utcnow()

    result = await users_collection.insert_one(user_dict)
    return JSONResponse(status_code=201, content={"msg": "User created", "user_id": str(result.inserted_id)})

# POST /login
@user_router.post("/login")
async def login(credentials: UserLogin):
    user = await users_collection.find_one({"email": credentials.email})
    await verify_recaptcha(credentials.recaptcha_response)
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token_data = {
        "sub": str(user["_id"]),
        "username": user["username"],
        "role": user["role"]
    }
    token = create_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


# GET /users (admin only)
@user_router.get("/users")
async def list_users(admin=Depends(admin_required)):
    users = await users_collection.find().to_list(100)
    return [
        {
            "id": str(u["_id"]),
            "username": u["username"],
            "email": u["email"],
            "role": u["role"]
        } for u in users
    ]


# PUT /users/{id}/make-admin (admin only)
@user_router.put("/users/{user_id}/make-admin")
async def make_admin(user_id: str, admin=Depends(admin_required)):
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": "admin"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"msg": "User promoted to admin"}

# DELETE /users/{id} (admin only)
@user_router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin=Depends(admin_required)):
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"msg": "User deleted"}



# GET /account (authenticated user)
@user_router.get("/account")
async def get_account(user=Depends(get_current_user)):
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"].isoformat()
    }


# PUT /account/password (authenticated user)
class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

@user_router.put("/account/password")
async def change_password(data: PasswordChangeRequest, user=Depends(get_current_user)):
    if not verify_password(data.old_password, user["hashed_password"]):
        raise HTTPException(status_code=403, detail="Incorrect old password")

    hashed_new = hash_password(data.new_password)
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": hashed_new}}
    )
    return {"msg": "Password updated successfully"}


# GET /dashboard (redirect based on role)
@user_router.get("/dashboard")
async def dashboard_redirect(user=Depends(get_current_user)):
    if user["role"] == "admin":
        return RedirectResponse(url="/dashboard/admin")
    return RedirectResponse(url="/dashboard/user")

# GET /dashboard/admin
@user_router.get("/dashboard/admin")
async def admin_dashboard(admin=Depends(admin_required)):
    return {
        "msg": f"Welcome Admin {admin['username']}",
        "links": [
            {"label": "Create Shipment", "url": "/api/shipments"},
            {"label": "Manage Users", "url": "/api/users"},
            {"label": "Manage Shipments", "url": "/api/shipments/all"},
            {"label": "Logout", "url": "/logout"}  # handled client-side
        ]
    }

# GET /dashboard/user
@user_router.get("/dashboard/user")
async def user_dashboard(user=Depends(get_current_user)):
    return {
        "msg": f"Welcome {user['username']}",
        "links": [
            {"label": "Create Shipment", "url": "/api/shipments"},
            {"label": "My Shipments", "url": "/api/shipments"},
            {"label": "Account Details", "url": "/api/account"},
            {"label": "Logout", "url": "/logout"}  # handled client-side
        ]
    }

# GET /logout (handled client-side)
@user_router.get("/logout")
async def logout():
    return JSONResponse(status_code=200, content={"msg": "Logged out successfully. Please clear your token from client."})




@user_router.get("/manage-users", dependencies=[Depends(admin_required)])
async def get_all_users():
    users = await users_collection.find().to_list(100)
    result = []
    for user in users:
        result.append({
            "id": str(user["_id"]),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else ""
        })
    return result

@user_router.put("/manage-users/{user_id}", dependencies=[Depends(admin_required)])
async def update_user(user_id: str, data: dict):
    update_fields = {}
    if "username" in data:
        update_fields["username"] = data["username"]
    if "email" in data:
        update_fields["email"] = data["email"]

    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"msg": "User updated"}


@user_router.put("/manage-users/{user_id}/promote", dependencies=[Depends(admin_required)])
async def promote_user(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] == "admin":
        raise HTTPException(status_code=400, detail="User is already an admin")

    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": "admin"}}
    )
    return {"msg": "User promoted to admin"}


@user_router.delete("/manage-users/{user_id}", dependencies=[Depends(admin_required)])
async def delete_user(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin user")

    await users_collection.delete_one({"_id": ObjectId(user_id)})
    return {"msg": "User deleted"}


@user_router.get("/account")
async def get_account(user=Depends(get_current_user)):
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"].isoformat()
    }
