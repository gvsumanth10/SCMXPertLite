import json
from kafka import KafkaConsumer
from pymongo import MongoClient
import sys
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

username = quote_plus(os.getenv('MONGO_USERNAME'))
password = quote_plus(os.getenv('MONGO_PASSWORD'))
cluster_name = os.getenv('MONGO_CLUSTER_NAME', 'trailcluster')
DB_NAME = os.getenv("MONGO_DB_NAME", "SCMLite")

# Kafka configuration
KAFKA_BROKER = 'kafka:9092'  # Replace with your Kafka broker address if different
KAFKA_TOPIC = 'sensor_data_topic'
KAFKA_GROUP_ID = 'sensor_data_group' # Consumer group ID

# MongoDB configuration
MONGO_URI = f'mongodb+srv://{username}:{password}@{cluster_name}.f5n8za4.mongodb.net/?retryWrites=true&w=majority&appName={cluster_name}'# Replace with your MongoDB URI if different
MONGO_DB = os.getenv('MONGO_DB_NAME')  # Your database name
MONGO_COLLECTION = 'sensor_data' # Your collection name

def start_consumer():
    consumer = None
    mongo_client = None
    try:
        # Initialize Kafka Consumer
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest', # Start reading at the earliest message available
            enable_auto_commit=True,
            group_id=KAFKA_GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print(f"[CONSUMER] Connected to Kafka broker at {KAFKA_BROKER}, consuming from topic '{KAFKA_TOPIC}'")

        # Initialize MongoDB Client
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        print(f"[CONSUMER] Connected to MongoDB at {MONGO_URI}, database '{MONGO_DB}', collection '{MONGO_COLLECTION}'")

        # Consume messages from Kafka
        for message in consumer:
            sensor_data = message.value
            print("\nReceived sensor data:")
            print(f"Device ID: {sensor_data.get('Device_ID')}")
            print(f"Battery Level: {sensor_data.get('Battery_Level')}V")
            print(f"Temperature: {sensor_data.get('First_Sensor_temperature')}°C")
            print(f"Route: {sensor_data.get('Route_From')} \u2192 {sensor_data.get('Route_To')}") # Unicode arrow

            # Insert data into MongoDB
            try:
                collection.insert_one(sensor_data)
                print("Data successfully stored in MongoDB.")
            except Exception as e:
                print(f"Error storing data in MongoDB: {e}")

    except Exception as e:
        print(f"Error in consumer: {e}")
        # Handle specific connection errors
        if "ConnectionRefusedError" in str(e) or "kafka.errors.NoBrokersAvailable" in str(e):
            print("Kafka broker or MongoDB might not be running or accessible.")
        elif "ServerSelectionTimeoutError" in str(e):
            print("Could not connect to MongoDB. Check if MongoDB is running.")
    finally:
        if consumer:
            consumer.close()
            print("[CONSUMER] Kafka consumer closed.")
        if mongo_client:
            mongo_client.close()
            print("[CONSUMER] MongoDB connection closed.")

if __name__ == "__main__":
    start_consumer()
