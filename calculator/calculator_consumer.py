from confluent_kafka import Consumer, KafkaException, KafkaError
import time

# Configuration for Kafka consumer
consumer_config = {
    'bootstrap.servers': 'localhost:9092',
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
            msgValue = msg.value().decode('utf-8')
            print(f"Consumed message: {msg.value().decode('utf-8')} from {msg.topic()}")

    except KeyboardInterrupt:
        print("Consumer interrupted by user.")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_messages()
