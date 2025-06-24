from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId # For handling MongoDB's default _id
from core.mongo import db # Changed: Import 'db' directly from mongo.py

# Pydantic model for the sensor data structure
class SensorData(BaseModel):
    # Use Field(alias="_id") for mapping "_id" from MongoDB to "id" in Pydantic
    # default_factory=lambda: str(ObjectId()) generates a new ObjectId string if not provided
    id: Optional[str] = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    Device_ID: int
    Battery_Level: float
    First_Sensor_temperature: float
    Route_From: str
    Route_To: str
    # Use default_factory=datetime.utcnow for automatic UTC timestamp generation
    Timestamp_IST: datetime = Field(default_factory=datetime.utcnow)

    # Configuration for Pydantic model
    class Config:
        populate_by_name = True  # Allow population by field name or alias
        json_encoders = {ObjectId: str} # Encode ObjectId to string when serializing to JSON
        arbitrary_types_allowed = True # Allows types like ObjectId to be used in model


class DeviceModel:
    """
    Manages database operations for sensor data in the "sensor_data" MongoDB collection.
    """
    def __init__(self):
        # Changed: Assign the directly imported 'db' from core.mongo
        self.db = db
        # Use the collection name as defined in mongo.py
        self.collection = self.db["sensor_data"] #
        # Optional: Create an index for efficient queries on Device_ID and timestamp
        self.collection.create_index([("Device_ID", 1), ("timestamp", -1)])

    async def create_sensor_reading(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Inserts a new sensor data reading into the collection.
        Args:
            data (Dict[str, Any]): A dictionary containing the sensor data.
                                   Expected keys: Device_ID, Battery_Level,
                                   First_Sensor_temperature, Route_From, Route_To.
        Returns:
            Optional[str]: The string representation of the inserted document's ID,
                           or None if an error occurred.
        """
        try:
            result = await self.collection.insert_one(data)
            print(f"Inserted sensor data with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error inserting sensor data: {e}")
            return None

    async def get_all_sensor_data(self) -> List[Dict[str, Any]]:
        """
        Retrieves all sensor data readings from the collection.
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a sensor data document. _id is converted to string.
        """
        try:
            # Fetch all documents and convert ObjectId to string for JSON serialization
            data = await self.collection.find({}).to_list(None) # .find({}) retrieves all documents
            for item in data:
                item['_id'] = str(item['_id'])
            return data
        except Exception as e:
            print(f"Error retrieving all sensor data: {e}")
            return []

    async def get_sensor_data_by_device_id(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves historical sensor data for a specific device ID, sorted by timestamp (latest first).
        Args:
            device_id (int): The ID of the device to retrieve data for.
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing sensor data for the specified device.
        """
        try:
            data = await self.collection.find({"Device_ID": device_id}).sort("timestamp", -1).to_list(None)
            for item in data:
                item['_id'] = str(item['_id'])
            return data
        except Exception as e:
            print(f"Error retrieving sensor data for device {device_id}: {e}")
            return []

    async def get_latest_sensor_reading(self, device_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest sensor reading for a specific device ID.
        Args:
            device_id (int): The ID of the device to retrieve the latest reading for.
        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the latest sensor reading,
                                     or None if no data is found for the device.
        """
        try:
            latest_reading = await self.collection.find_one(
                {"Device_ID": device_id}, sort=[("timestamp", -1)] # Sort descending to get the latest
            )
            if latest_reading:
                latest_reading['_id'] = str(latest_reading['_id'])
            return latest_reading
        except Exception as e:
            print(f"Error retrieving latest sensor reading for device {device_id}: {e}")
            return None

# Instantiate the DeviceModel for easy import and use in FastAPI routes
device_model = DeviceModel()