from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from models.shipment_model import ShipmentCreate, ShipmentOut
from core.mongo import shipments_collection, users_collection
from core.auth import get_current_user, admin_required
from bson import ObjectId
from datetime import datetime
import os

router = APIRouter()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


# GET /shipments/all (admin only)
@router.get("/shipments/all")
async def get_all_shipments(admin=Depends(admin_required)):
    shipments = await shipments_collection.find().to_list(100)
    for s in shipments:
        s["_id"] = str(s["_id"])
        s["created_by"]["id"] = str(s["created_by"]["id"])
        s["created_at"] = s["created_at"].isoformat()
    return shipments



# POST /api/shipments
@router.post("/shipments", status_code=201)
async def create_shipment(shipment: ShipmentCreate, user=Depends(get_current_user)):
    shipment_data = shipment.dict()
    shipment_data["created_by"] = {
        "id": user["_id"],
        "username": user["username"],
        "role": user["role"]
    }
    shipment_data["created_at"] = datetime.utcnow()

    result = await shipments_collection.insert_one(shipment_data)
    return {"msg": "Shipment created", "shipment_id": str(result.inserted_id)}


# PUT /shipments/{id}/edit (admin only)
@router.put("/shipments/{shipment_id}/edit")
async def edit_shipment(shipment_id: str, updated: ShipmentCreate, admin=Depends(admin_required)):
    result = await shipments_collection.update_one(
        {"_id": ObjectId(shipment_id)},
        {"$set": updated.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {"msg": "Shipment updated"}


# DELETE /shipments/{id} (admin only)
@router.delete("/shipments/{shipment_id}")
async def delete_shipment(shipment_id: str, admin=Depends(admin_required)):
    result = await shipments_collection.delete_one({"_id": ObjectId(shipment_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {"msg": "Shipment deleted"}



# Helper to decode JWT and fetch user info
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid")

# POST /api/shipments
@router.post("/shipments", status_code=201)
async def create_shipment(shipment: ShipmentCreate, user=Depends(get_current_user)):
    shipment_data = shipment.dict()
    shipment_data["created_by"] = {
        "id": user["_id"],
        "username": user["username"],
        "role": user["role"]
    }
    shipment_data["created_at"] = datetime.utcnow()

    result = await shipments_collection.insert_one(shipment_data)
    return {"msg": "Shipment created", "shipment_id": str(result.inserted_id)}



@router.get("/shipments/mine")
async def get_my_shipments(user=Depends(get_current_user)):
    shipments = await shipments_collection.find({
        "created_by.id": user["_id"]
    }).to_list(100)

    serialized_shipments = []
    for s in shipments:
        serialized_shipments.append({
            "shipment_number": str(s.get("shipment_number")),
            "route": s.get("route", ""),
            "device": s.get("device", ""),
            "goods_type": s.get("goods_type", ""),
            "delivery_date": s.get("delivery_date", ""),
            "status": s.get("status", ""),
        })

    return serialized_shipments


# GET /shipments (admin)
@router.get("/shipments", dependencies=[Depends(admin_required)])
async def get_all_shipments():
    shipments = await shipments_collection.find().to_list(100)

    result = []
    for s in shipments:
        result.append({
            "id": str(s["_id"]),
            "shipment_number": s.get("shipment_number", ""),
            "route": s.get("route", ""),
            "goods_type": s.get("goods_type", ""),
            "device": s.get("device", ""),
            "delivery_date": s.get("delivery_date", ""),
            "status": s.get("status", ""),
            "created_by": s.get("created_by", {}).get("username", ""),
        })
    return result

# PUT /shipments/{id}
@router.put("/shipments/{shipment_id}", dependencies=[Depends(admin_required)])
async def update_shipment(shipment_id: str, updates: dict):
    result = await shipments_collection.update_one(
        {"_id": ObjectId(shipment_id)},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {"msg": "Shipment updated successfully"}


# DELETE /shipments/{id}
@router.delete("/shipments/{shipment_id}", dependencies=[Depends(admin_required)])
async def delete_shipment(shipment_id: str):
    result = await shipments_collection.delete_one({"_id": ObjectId(shipment_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {"msg": "Shipment deleted"}