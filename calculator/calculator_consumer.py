from confluent_kafka import Consumer, KafkaException, KafkaError
from prometheus_kafka_consumer.metrics_manager import ConsumerMetricsManager  # For monitoring Kafka consumer metrics
from prometheus_client import start_http_server  # For exposing Prometheus metrics
import requests  # For making HTTP requests to the FastAPI service
import os  # For accessing environment variables
import ssl  # For SSL/TLS configuration
import urllib3  # For managing HTTP connections
# Disable SSL warnings for self-signed certificates in development environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Get configuration from environment variables with fallback values
Kafkasever = os.getenv("KAFKA_BROKER_URL", "localhost:9092")  # Kafka server address
Fastapi = os.getenv("FASTAPI_SERVER", "https://localhost:8000")  # FastAPI server address (HTTPS)
api_key = os.getenv("SERVICE_API_KEY", "")  # API key for authentication with FastAPI

# Configure the Kafka consumer
consumer_config = {
    'bootstrap.servers': Kafkasever,  # Kafka broker addresses
    'group.id': 'consumer-microservice',  # Consumer group ID for load balancing
    'auto.offset.reset': 'earliest',  # Start reading from the beginning if no offset is stored
}

# Initialize Kafka consumer with the configuration
consumer = Consumer(consumer_config)

def consume_messages():
    """
    Main function that consumes messages from Kafka topic,
    processes them, and sends the results to the FastAPI service.
    """
    topic = "calculator_topic"  # Topic to subscribe to
    consumer.subscribe([topic])  # Subscribe to the topic
    
    try:
        while True:  # Continuous polling loop
            # Poll for messages with a 1-second timeout
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:  # No message received
                continue
                
            if msg.error():  # Handle message errors
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event, not an error in this case
                    continue
                else:
                    # Actual error occurred
                    print(f"Consumer error: {msg.error()}")
                    break
            
            # Process the successfully received message
            msg_value = msg.value().decode('utf-8')  # Convert bytes to string
            print(f"Consumed message: {msg_value} from {msg.topic()}")

            # Parse the CSV-formatted message (num1,num2,result)
            values = msg_value.split(',')
            num1 = float(values[0])  # First number
            num2 = float(values[1])  # Second number
            result = float(values[2])  # Calculation result

            # Prepare request headers with API key if available
            headers = {"X-API-Key": api_key} if api_key else {}
            
            # Create session for better connection management
            session = requests.Session()
            session.verify = False  # Skip SSL verification for self-signed certs
    
            # Send the calculation data to FastAPI service
            response = session.post(
                Fastapi + "/store_calculation",  # Endpoint URL
                json={"num1": num1, "num2": num2, "result": result},  # Request payload
                headers=headers,  # Authentication headers
                timeout=5  # Request timeout in seconds
            )
            # Log the response details
            print(f"Status code: {response.status_code}, Response: {response.text}")

    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C
        print("Consumer interrupted by user.")
    finally:
        # Always close the consumer to release resources
        consumer.close()

# Entry point of the script
if __name__ == "__main__":
    consume_messages()