import grpc
import calculator_pb2
import calculator_pb2_grpc
import random
import time
import os

def run():
    grpc_url = os.getenv("GRPC_SERVER_URL", "localhost:50051")
    
    # Load TLS credentials
    with open('/app/certs/cert.pem', 'rb') as f:
        trusted_certs = f.read()
    
    # Create SSL credentials with server name override
    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
    
    # Create secure channel with server name override option
    options = (('grpc.ssl_target_name_override', 'server'),)
    with grpc.secure_channel(grpc_url, credentials, options) as channel:
        stub = calculator_pb2_grpc.CalculatorStub(channel)
        while True:
            num1 = round(random.uniform(1, 100), 1)
            num2 = round(random.uniform(1, 100), 1)
            response = stub.Add(calculator_pb2.AddRequest(num1=num1, num2=num2))
            print(f"Sent: num1={num1}, num2={num2} | Result: {response.result}")
            time.sleep(5)

if __name__ == "__main__":
    run()