from confluent_kafka import Producer
import time

# Configuration for Kafka producer
producer_config = {
    'bootstrap.servers': 'localhost:9092',  # Kafka broker
    'client.id': 'producer-microservice',
}

# Initialize Kafka producer
producer = Producer(producer_config)

def delivery_report(err, msg):
    """Callback to confirm message delivery or handle errors."""
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def produce_messages():
    topic = "example_topic"
    counter = 0
    while True:
        message = f"Sample message {counter}"
        try:
            producer.produce(topic, value=message, callback=delivery_report)
        except BufferError:
            print("Buffer full, retrying...")
            time.sleep(1)
            producer.produce(topic, value=message, callback=delivery_report)
        producer.poll(0)  # Trigger callbacks
        print(f"Sent: {message}")
        counter += 1
        time.sleep(5)  # Wait for 5 seconds before sending the next message

if __name__ == "__main__":
    produce_messages()
