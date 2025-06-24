# core/auth.py
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from core.mongo import users_collection
from bson import ObjectId
import os
import requests

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)) # Default to 1 hour

reCAPTCHA_SECRET_KEY = os.getenv('SECRET_KEY')
reCAPTCHA_VERIFY_URL = os.getenv('reCAPTCHA_VERIFY_URL')

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid")

async def admin_required(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return user


async def verify_recaptcha(recaptcha_response: str):
    if not reCAPTCHA_SECRET_KEY:
        raise HTTPException(status_code=500, detail="reCAPTCHA secret key not configured.")

    payload = {
        "secret": reCAPTCHA_SECRET_KEY,
        "response": recaptcha_response
    }
    response = requests.post(reCAPTCHA_VERIFY_URL, data=payload)
    result = response.json()
    print(f"reCAPTCHA verification result: {result}") # Add this line for debugging

    if not result.get("success"):
        error_codes = result.get("error-codes", [])
        print(f"reCAPTCHA error codes: {error_codes}") # Log error codes
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed. Please try again.")
    return True