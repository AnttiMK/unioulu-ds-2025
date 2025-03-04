import grpc
import calculator_pb2
import calculator_pb2_grpc
import random
import time
import os

def run():
    grpc_url = os.getenv("GRPC_SERVER_URL", "localhost:50051")
    with grpc.insecure_channel(grpc_url) as channel:
        stub = calculator_pb2_grpc.CalculatorStub(channel)
        while True:
            num1 = round(random.uniform(1, 100), 1)
            num2 = round(random.uniform(1, 100), 1)
            response = stub.Add(calculator_pb2.AddRequest(num1=num1, num2=num2))
            print(f"Sent: num1={num1}, num2={num2} | Result: {response.result}")
            time.sleep(2)

if __name__ == "__main__":
    run()