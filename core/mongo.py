import motor.motor_asyncio
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

username = quote_plus(os.getenv('MONGO_USERNAME'))
password = quote_plus(os.getenv('MONGO_PASSWORD'))
cluster_name = os.getenv('MONGO_CLUSTER_NAME', 'trailcluster')
DB_NAME = os.getenv("MONGO_DB_NAME", "SCMLite")
uri = f'mongodb+srv://{username}:{password}@{cluster_name}.f5n8za4.mongodb.net/?retryWrites=true&w=majority&appName={cluster_name}'


# MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster_name}/{DB_NAME}?retryWrites=true&w=majority"
client = motor.motor_asyncio.AsyncIOMotorClient(uri)
db=client[DB_NAME]

users_collection = db['users']
shipments_collection = db['shipments']
logins_collection = db['logins']
sensor_data_collection = db['sensor_data']


