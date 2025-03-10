from locust import HttpUser, task, between  # Locust for load testing
import grpc  # For gRPC communications
import json  # For JSON handling
import random  # For generating random numbers
import time  # For timing operations
import sys  # For modifying Python path
import os  # For environment variables
import ssl  # For SSL configurations
import warnings  # For suppressing warnings

# Suppress SSL warnings for self-signed certificates
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Add the project root to the path so we can import the modules correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import the gRPC modules with the correct path
from calculator.calculator_pb2 import AddRequest  # Import the generated request message type
from calculator.calculator_pb2_grpc import CalculatorStub  # Import the generated client stub

class CalculatorUser(HttpUser):
    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)  # Simulates realistic user behavior with random waits
    
    def on_start(self):
        """Initialize the gRPC channel when a user starts"""
        # Create a gRPC channel to the server
        grpc_host = os.environ.get("GRPC_SERVER_URL", "localhost:50051")  # Get server address from env vars
        
        # Load SSL credentials for secure gRPC
        with open('/app/certs/cert.pem', 'rb') as f:
            trusted_certs = f.read()  # Read the PEM-encoded certificate
            
        # Create SSL credentials
        credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
        
        # Create secure channel with server name override
        options = (('grpc.ssl_target_name_override', 'server'),)  # Override hostname check
        self.grpc_channel = grpc.secure_channel(grpc_host, credentials, options)
        self.calculator_stub = CalculatorStub(self.grpc_channel)  # Create the gRPC client stub
        
        # Set API key for HTTP requests
        api_key = os.environ.get("SERVICE_API_KEY", "")
        if api_key:
            self.client.headers.update({"X-API-Key": api_key})  # Add to all HTTP requests
        
        # Disable SSL verification for self-signed certificates in development
        self.client.verify = False  # Skip SSL certificate verification for HTTP requests

    def on_stop(self):
        """Close the gRPC channel when a user stops"""
        if hasattr(self, 'grpc_channel'):
            self.grpc_channel.close()  # Clean up resources
    
    @task(2)  # Higher weight means this task runs more frequently
    def get_calculations(self):
        """Task to get calculations from FastAPI"""
        try:
            with self.client.get("/calculations", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()  # Mark as successful in Locust statistics
                else:
                    response.failure(f"Failed with status code: {response.status_code}")  # Mark as failure
        except Exception as e:
            print(f"Error during get_calculations: {str(e)}")
    
    @task(1)  # Lower weight means this task runs less frequently
    def grpc_add_calculation(self):
        """Task to send calculation request via gRPC"""
        try:
            # Generate random numbers for the addition operation
            num1 = round(random.uniform(1, 100), 1)  # Random number between 1-100 with 1 decimal
            num2 = round(random.uniform(1, 100), 1)
            
            # Make gRPC call and measure execution time
            start_time = time.time()
            response = self.calculator_stub.Add(AddRequest(num1=num1, num2=num2))
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Record the event with Locust for statistics
            self.environment.events.request.fire(
                request_type="grpc",  # Type of request
                name="Calculator/Add",  # Name of the endpoint
                response_time=execution_time,  # Response time in ms
                response_length=0,  # No content length for gRPC
                exception=None,  # No exception occurred
            )
            
            print(f"gRPC Add: {num1} + {num2} = {response.result}")
            
        except Exception as e:
            # Record failed request with Locust for statistics
            self.environment.events.request.fire(
                request_type="grpc",
                name="Calculator/Add",
                response_time=0,
                response_length=0,
                exception=e,  # Include the exception that occurred
            )
            print(f"gRPC error: {str(e)}")