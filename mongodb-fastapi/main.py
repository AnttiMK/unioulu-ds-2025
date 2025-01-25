from fastapi import FastAPI
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
import os
from prometheus_client import start_http_server, Summary, Counter, Gauge
from prometheus_client.exposition import generate_latest
from fastapi.responses import PlainTextResponse

app = FastAPI()

mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:password@localhost:27017")

# Start Prometheus metrics server
start_http_server(8001)

# Define metrics
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
REQUEST_COUNT = Counter('request_count', 'Total number of requests')
IN_PROGRESS = Gauge('in_progress_requests', 'Number of requests in progress')

@app.middleware("http")
async def add_metrics(request, call_next):
    REQUEST_COUNT.inc()
    IN_PROGRESS.inc() 
    with REQUEST_TIME.time():
        response = await call_next(request)
    IN_PROGRESS.dec()
    return response

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())


# MongoDB connection
client = AsyncIOMotorClient(mongodb_url)
db = client.calculations_db
collection = db.calculations

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI and MongoDB!"}

# Pydantic models
class CalculationRequest(BaseModel):
    num1: float = Field(..., description="The first number for the addition")
    num2: float = Field(..., description="The second number for the addition")
    result: float = Field(..., description="The result of the addition")

class CalculationResponse(BaseModel):
    num1: float
    num2: float
    result: float

@app.post("/store_calculation", response_model=CalculationResponse)
async def store_calculation(request: CalculationRequest):
    # Store the request and result in MongoDB
    calculation = {
        "num1": request.num1,
        "num2": request.num2,
        "result": request.result
    }
    await collection.insert_one(calculation)
    
    return request

@app.get("/calculations", response_model=List[CalculationResponse])
async def get_calculations():
    calculations = []
    async for calculation in collection.find():
        calculations.append(CalculationResponse(**calculation))
    return calculations
