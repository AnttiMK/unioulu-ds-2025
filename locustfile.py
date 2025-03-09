from locust import HttpUser, task, between
import grpc
import json
import random
import time
import sys
import os

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
        self.grpc_channel = grpc.insecure_channel(grpc_host)
        self.calculator_stub = CalculatorStub(self.grpc_channel)
        
        # Set API key for HTTP requests
        api_key = os.environ.get("SERVICE_API_KEY", "")
        if api_key:
            self.client.headers.update({"X-API-Key": api_key})

    def on_stop(self):
        """Close the gRPC channel when a user stops"""
        self.grpc_channel.close()

    @task(3)
    def test_grpc_calculator(self):
        """Test the gRPC calculator service with a higher weight"""
        # Generate random numbers for the request
        num1 = round(random.uniform(1, 100), 1)
        num2 = round(random.uniform(1, 100), 1)

        # Create request timing for Locust
        start_time = time.time()
        try:
            # Call the gRPC method
            response = self.calculator_stub.Add(AddRequest(num1=num1, num2=num2))
            
            # Record the result
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="grpc",
                name="Calculator/Add",
                response_time=total_time,
                response_length=0,
                exception=None,
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="grpc",
                name="Calculator/Add",
                response_time=total_time,
                response_length=0,
                exception=e,
            )

    @task(2)
    def get_calculations(self):
        """Test the REST API endpoint for retrieving calculations"""
        self.client.get("/calculations")
    
    @task(1)
    def store_calculation_direct(self):
        """Test direct storage of calculations via REST API"""
        num1 = round(random.uniform(1, 100), 1)
        num2 = round(random.uniform(1, 100), 1)
        result = num1 + num2
        
        payload = {
            "num1": num1,
            "num2": num2,
            "result": result
        }
        self.client.post("/store_calculation", json=payload)

    @task
    def check_metrics(self):
        """Test the metrics endpoint"""
        self.client.get("/metrics")