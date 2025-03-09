from concurrent import futures
import grpc
import calculator_pb2
import calculator_pb2_grpc
from confluent_kafka import Producer
from prometheus_client import start_http_server, Summary, Counter, Gauge
from prometheus_client.exposition import generate_latest
from prometheus_kafka_producer.metrics_manager import ProducerMetricsManager
from grpc_reflection.v1alpha import reflection
import os

KafkaServer = os.getenv("KAFKA_BROKER_URL", "localhost:9092")

# Start Prometheus metrics server for gRPC (8001)
start_http_server(8001)


"""
# Define metrics
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
REQUEST_COUNT = Counter('request_count', 'Total number of requests')
IN_PROGRESS = Gauge('in_progress_requests', 'Number of requests in progress')
"""
# Configuration for Kafka producer
producer_config = {
    'bootstrap.servers': KafkaServer,  # Kafka broker
    'client.id': 'calculator-server',
}

# Initialize Kafka producer
producer = Producer(producer_config)

def delivery_report(err, msg):
    """Callback to confirm message delivery or handle errors."""
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

class CalculatorServicer(calculator_pb2_grpc.CalculatorServicer):
    def Add(self, request, context):
        result = request.num1 + request.num2
        response = calculator_pb2.AddResponse(result=result)
        
        # Produce message to Kafka
        message = f"{request.num1},{request.num2},{result}"
        producer.produce('calculator_topic', value=message, callback=delivery_report)
        producer.poll(0)  # Trigger delivery report callbacks
        print(f"Sent: {message}")
        
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    calculator_pb2_grpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    SERVICE_NAMES = (
        calculator_pb2.DESCRIPTOR.services_by_name['Calculator'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server is running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()