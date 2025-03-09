from confluent_kafka import Consumer, KafkaException, KafkaError
from prometheus_kafka_consumer.metrics_manager import ConsumerMetricsManager
from prometheus_client import start_http_server
import requests
import os
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

Kafkasever = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
Fastapi = os.getenv("FASTAPI_SERVER", "https://localhost:8000")  # Changed to https
api_key = os.getenv("SERVICE_API_KEY", "")

consumer_config = {
    'bootstrap.servers': Kafkasever,
    'group.id': 'consumer-microservice',
    'auto.offset.reset': 'earliest',
}

# Initialize Kafka consumer
consumer = Consumer(consumer_config)

def consume_messages():
    topic = "calculator_topic"
    consumer.subscribe([topic])
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break
            
            # Process the message
            msg_value = msg.value().decode('utf-8')
            print(f"Consumed message: {msg.value().decode('utf-8')} from {msg.topic()}")

            values = msg_value.split(',')
            num1 = float(values[0])
            num2 = float(values[1])
            result = float(values[2])

            # Add API key to headers
            headers = {"X-API-Key": api_key} if api_key else {}
            
            session = requests.Session()
            session.verify = False  # For self-signed certificates
    
    # Use the session for requests
            response = session.post(
                Fastapi + "/store_calculation",
                json={"num1": num1, "num2": num2, "result": result},
                headers=headers,
                timeout=5
            )
            print(f"Status code: {response.status_code}, Response: {response.text}")

    except KeyboardInterrupt:
        print("Consumer interrupted by user.")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_messages()