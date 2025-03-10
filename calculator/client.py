import grpc  # Library for gRPC communication
import calculator_pb2  # Auto-generated protobuf message classes
import calculator_pb2_grpc  # Auto-generated gRPC service definitions
import random  # For generating random numbers
import time  # For adding delays between requests
import os  # For accessing environment variables

def run():
    # Get the gRPC server URL from environment variables with a fallback value
    grpc_url = os.getenv("GRPC_SERVER_URL", "localhost:50051")
    
    # Load TLS/SSL certificate for secure communication
    with open('/app/certs/cert.pem', 'rb') as f:
        trusted_certs = f.read()  # Read the certificate file contents
    
    # Create SSL credentials using the loaded certificate
    # This authenticates the server to the client
    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
    
    # Options for the gRPC channel - override target hostname for certificate validation
    # This allows the client to validate the certificate even if hostname doesn't match
    options = (('grpc.ssl_target_name_override', 'server'),)
    
    # Establish a secure connection to the gRPC server
    with grpc.secure_channel(grpc_url, credentials, options) as channel:
        # Create a client-side stub to make RPC calls
        stub = calculator_pb2_grpc.CalculatorStub(channel)
        
        # Infinite loop to continuously send calculation requests
        while True:
            # Generate random decimal numbers between 1 and 100 with 1 decimal place
            num1 = round(random.uniform(1, 100), 1)
            num2 = round(random.uniform(1, 100), 1)
            
            # Make the RPC call to the Add method, passing the numbers in a request object
            response = stub.Add(calculator_pb2.AddRequest(num1=num1, num2=num2))
            
            # Print the request values and the server's response
            print(f"Sent: num1={num1}, num2={num2} | Result: {response.result}")
            
            # Wait 5 seconds before sending the next request
            time.sleep(5)

# Standard Python idiom to check if this script is being run directly
if __name__ == "__main__":
    run()