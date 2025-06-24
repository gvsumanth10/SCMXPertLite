from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
from models.device_model import device_model # Import the instantiated DeviceModel
from core.auth import admin_required # Import admin_required dependency

router = APIRouter()

# GET all sensor data (admin only)
@router.get("/devices/sensor_data", response_model=List[Dict[str, Any]])
async def get_all_sensor_data(admin: dict = Depends(admin_required)):
    """
    Retrieves all sensor data readings from the database.
    Requires admin privileges.
    """
    try:
        data = await device_model.get_all_sensor_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve device data: {e}")

# GET latest sensor data for a specific device (admin only)
@router.get("/devices/{device_id}/latest_sensor_data", response_model=Optional[Dict[str, Any]])
async def get_latest_device_sensor_data(
    device_id: int,
    admin: dict = Depends(admin_required)
):
    """
    Retrieves the latest sensor data reading for a specific device ID.
    Requires admin privileges.
    """
    try:
        data = await device_model.get_latest_sensor_reading(device_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sensor data found for this device ID")
        return data
    except HTTPException as he:
        raise he # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve latest device data: {e}")

# GET historical sensor data for a specific device (admin only)
@router.get("/devices/{device_id}/sensor_history", response_model=List[Dict[str, Any]])
async def get_device_sensor_history(
    device_id: int,
    admin: dict = Depends(admin_required)
):
    """
    Retrieves all historical sensor data readings for a specific device ID.
    Requires admin privileges.
    """
    try:
        data = await device_model.get_sensor_data_by_device_id(device_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No historical sensor data found for this device ID")
        return data
    except HTTPException as he:
        raise he # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve device history data: {e}")