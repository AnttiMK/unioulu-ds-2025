from concurrent import futures
import grpc
import calculator_pb2
import calculator_pb2_grpc
from confluent_kafka import Producer
from prometheus_client import start_http_server, Summary, Counter, Gauge
from py_grpc_prometheus.prometheus_server_interceptor import PromServerInterceptor
from grpc_reflection.v1alpha import reflection
import os
import requests

KafkaServer = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
api_key = os.getenv("SERVICE_API_KEY", "")

# Start Prometheus metrics server for gRPC (8001)
start_http_server(8001)

# Configuration for Kafka producer
producer_config = {
    'bootstrap.servers': KafkaServer,
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
    # Load TLS credentials
    with open('/app/certs/key.pem', 'rb') as f:
        private_key = f.read()
    with open('/app/certs/cert.pem', 'rb') as f:
        certificate_chain = f.read()
    
    # Create server credentials
    server_credentials = grpc.ssl_server_credentials(
        [(private_key, certificate_chain)]
    )
    
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=(PromServerInterceptor(enable_handling_time_histogram=True),),
        options=[
            ('grpc.ssl_target_name_override', 'server'),
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024)
        ]
    )
    
    calculator_pb2_grpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    SERVICE_NAMES = (
        calculator_pb2.DESCRIPTOR.services_by_name['Calculator'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    
    # Use secure port instead of insecure
    server.add_secure_port('[::]:50051', server_credentials)
    server.start()
    print("Secure server is running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()