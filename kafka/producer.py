import json
import time
import random
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from datetime import datetime
import pytz # Import pytz for timezone handling

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'  # Replace with your Kafka broker address if different
KAFKA_TOPIC = 'sensor_data_topic'

# Define Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

def start_producer():
    producer = None
    try:
        # Initialize Kafka Producer
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print(f"[PRODUCER] Connected to Kafka broker at {KAFKA_BROKER}")

        # Limit to 20 messages
        messages_to_send = 20
        sent_count = 0

        while sent_count < messages_to_send:
            route = ['Newyork,USA', 'Chennai, India', 'Bengaluru, India', 'London,UK']
            route_from = random.choice(route)
            route_to = random.choice(route)

            # Ensure Route_From and Route_To are different
            if route_from == route_to:
                continue # Skip this iteration if routes are the same

            # Get current timestamp in IST
            current_ist_time = datetime.now(IST)

            data = {
                "Device_ID": random.randint(1150, 1158),
                "Battery_Level": round(random.uniform(2.00, 5.00), 2),
                "First_Sensor_temperature": round(random.uniform(10, 40.0), 1),
                "Route_From": route_from,
                "Route_To": route_to,
                "Timestamp_IST": current_ist_time.isoformat() # Add IST timestamp
            }

            # Send data to Kafka topic
            producer.send(KAFKA_TOPIC, value=data)
            print(f"Sent data ({sent_count+1}/{messages_to_send}) to topic '{KAFKA_TOPIC}': {data}")
            sent_count += 1 # Increment count only when a message is successfully sent

            # Sleep for 2 seconds before sending the next message
            time.sleep(2)

        print(f"\n[PRODUCER] Finished sending {sent_count} messages.")

    except NoBrokersAvailable:
        print(f"[PRODUCER ERROR] Could not connect to Kafka broker at {KAFKA_BROKER}. Is Kafka running?")
    except Exception as e:
        print(f"[PRODUCER ERROR] An unexpected error occurred: {e}")
    finally:
        if producer:
            producer.flush()  # Ensure all messages are sent
            producer.close()  # Close the producer connection
            print("[PRODUCER] Kafka producer closed.")

if __name__ == "__main__":
    start_producer()