from locust import HttpUser, task, between
import grpc
import json
import random
import time
import sys
import os
import ssl
import warnings

# Suppress SSL warnings for self-signed certificates
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Add the project root to the path so we can import the modules correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import the gRPC modules with the correct path
from calculator.calculator_pb2 import AddRequest
from calculator.calculator_pb2_grpc import CalculatorStub

class CalculatorUser(HttpUser):
    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize the gRPC channel when a user starts"""
        # Create a gRPC channel to the server
        grpc_host = os.environ.get("GRPC_SERVER_URL", "localhost:50051")
        
        # Load SSL credentials for secure gRPC
        with open('/app/certs/cert.pem', 'rb') as f:
            trusted_certs = f.read()
            
        # Create SSL credentials
        credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
        
        # Create secure channel with server name override
        options = (('grpc.ssl_target_name_override', 'server'),)
        self.grpc_channel = grpc.secure_channel(grpc_host, credentials, options)
        self.calculator_stub = CalculatorStub(self.grpc_channel)
        
        # Set API key for HTTP requests
        api_key = os.environ.get("SERVICE_API_KEY", "")
        if api_key:
            self.client.headers.update({"X-API-Key": api_key})
        
        # Disable SSL verification for self-signed certificates in development
        self.client.verify = False

    def on_stop(self):
        """Close the gRPC channel when a user stops"""
        if hasattr(self, 'grpc_channel'):
            self.grpc_channel.close()
    
    @task(2)
    def get_calculations(self):
        """Task to get calculations from FastAPI"""
        try:
            with self.client.get("/calculations", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed with status code: {response.status_code}")
        except Exception as e:
            print(f"Error during get_calculations: {str(e)}")
    
    @task(1)
    def grpc_add_calculation(self):
        """Task to send calculation request via gRPC"""
        try:
            num1 = round(random.uniform(1, 100), 1)
            num2 = round(random.uniform(1, 100), 1)
            
            # Make gRPC call
            start_time = time.time()
            response = self.calculator_stub.Add(AddRequest(num1=num1, num2=num2))
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Record the event with Locust
            self.environment.events.request.fire(
                request_type="grpc",
                name="Calculator/Add",
                response_time=execution_time,
                response_length=0,
                exception=None,
            )
            
            print(f"gRPC Add: {num1} + {num2} = {response.result}")
            
        except Exception as e:
            # Record failed request with Locust
            self.environment.events.request.fire(
                request_type="grpc",
                name="Calculator/Add",
                response_time=0,
                response_length=0,
                exception=e,
            )
            print(f"gRPC error: {str(e)}")