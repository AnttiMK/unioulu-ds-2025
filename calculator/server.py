from concurrent import futures  # For parallel execution using thread pools
import grpc  # For gRPC server implementation
import calculator_pb2  # Auto-generated protobuf message classes
import calculator_pb2_grpc  # Auto-generated gRPC service definitions
from confluent_kafka import Producer  # Kafka producer for sending calculation results
from prometheus_client import start_http_server, Summary, Counter, Gauge  # For metrics collection
from py_grpc_prometheus.prometheus_server_interceptor import PromServerInterceptor  # For gRPC metrics
from grpc_reflection.v1alpha import reflection  # For service reflection (service discovery)
import os  # For accessing environment variables
import requests  # For making HTTP requests (unused in this file)

# Get configuration from environment variables with fallback values
KafkaServer = os.getenv("KAFKA_BROKER_URL", "localhost:9092")  # Kafka broker address
api_key = os.getenv("SERVICE_API_KEY", "")  # API key for authentication with FastAPI

# Start Prometheus metrics server for gRPC on port 8001
# This exposes metrics about gRPC requests for monitoring
start_http_server(8001)

# Configuration for Kafka producer
producer_config = {
    'bootstrap.servers': KafkaServer,  # Kafka broker addresses
    'client.id': 'calculator-server',  # Unique ID for this producer
}

# Initialize Kafka producer with the configuration
producer = Producer(producer_config)

def delivery_report(err, msg):
    """Callback to confirm message delivery or handle errors."""
    if err:
        print(f"Message delivery failed: {err}")  # Log error if message delivery fails
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")  # Log successful delivery

class CalculatorServicer(calculator_pb2_grpc.CalculatorServicer):
    def Add(self, request, context):
        """Implementation of the Add RPC method defined in calculator.proto.
        
        This method adds two numbers and sends the result to a Kafka topic.
        
        Args:
            request: The AddRequest containing num1 and num2.
            context: The gRPC context for the call.
            
        Returns:
            An AddResponse with the calculation result.
        """
        # Perform addition operation
        result = request.num1 + request.num2
        response = calculator_pb2.AddResponse(result=result)
        
        # Produce message to Kafka in CSV format (num1,num2,result)
        message = f"{request.num1},{request.num2},{result}"
        producer.produce('calculator_topic', value=message, callback=delivery_report)
        producer.poll(0)  # Trigger delivery report callbacks without blocking
        print(f"Sent: {message}")  # Log the message sent to Kafka
        
        return response  # Return the result to the gRPC client

def serve():
    """Start and configure the gRPC server with TLS security.
    
    This function loads TLS certificates, configures the server with interceptors
    for metrics collection, registers the CalculatorServicer, and starts the server.
    """
    # Load TLS credentials for secure communication
    with open('/app/certs/key.pem', 'rb') as f:
        private_key = f.read()  # Server's private key
    with open('/app/certs/cert.pem', 'rb') as f:
        certificate_chain = f.read()  # Server's certificate
    
    # Create server credentials using the loaded key and certificate
    server_credentials = grpc.ssl_server_credentials(
        [(private_key, certificate_chain)]
    )
    
    # Create and configure the gRPC server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),  # Thread pool for handling concurrent requests
        interceptors=(PromServerInterceptor(enable_handling_time_histogram=True),),  # Add Prometheus metrics collection
        options=[
            ('grpc.ssl_target_name_override', 'server'),  # Override hostname for certificate validation
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # Max message size ~50MB
            ('grpc.max_receive_message_length', 50 * 1024 * 1024)  # Max message size ~50MB
        ]
    )
    
    # Register the Calculator service implementation with the server
    calculator_pb2_grpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    
    # Enable service reflection for service discovery
    SERVICE_NAMES = (
        calculator_pb2.DESCRIPTOR.services_by_name['Calculator'].full_name,  # Calculator service
        reflection.SERVICE_NAME,  # Reflection service
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    
    # Add a secure endpoint for the server to listen on (port 50051)
    server.add_secure_port('[::]:50051', server_credentials)
    
    # Start the server and log that it's running
    server.start()
    print("Secure server is running on port 50051")
    
    # Keep the server running until manually terminated
    server.wait_for_termination()

# Standard Python idiom to check if this script is being run directly
if __name__ == "__main__":
    serve()