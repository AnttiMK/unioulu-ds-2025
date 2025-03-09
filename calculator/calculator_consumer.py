from confluent_kafka import Consumer, KafkaException, KafkaError
import requests
import os

Kafkasever = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
Fastapi = os.getenv("FASTAPI_SERVER", "http://localhost:8000")
api_key = os.getenv("SERVICE_API_KEY", "")  # Add this line to get API key

# Configuration for Kafka consumer
consumer_config = {
    'bootstrap.servers': Kafkasever,
    'group.id': 'consumer-microservice',
    'auto.offset.reset': 'earliest',  # Start reading at the earliest message
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
            
            response = requests.post(
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