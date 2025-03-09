from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import os
from prometheus_client import start_http_server, Summary, Counter, Gauge
from prometheus_client.exposition import generate_latest
from fastapi.responses import PlainTextResponse
from prometheus_fastapi_instrumentator import Instrumentator
from policy_engine import policy_engine  # Import the policy engine

app = FastAPI()

mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:password@localhost:27017")

# Initiliaze Prometheus metrics server for FastAPI (8000)
Instrumentator().instrument(app).expose(app)

# MongoDB connection
client = AsyncIOMotorClient(mongodb_url)
db = client.calculations_db
collection = db.calculations

# API key verification dependency using policy engine
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="API Key is missing")
    
    if not policy_engine.is_valid_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    if not policy_engine.check_rate_limit(x_api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return x_api_key

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
async def store_calculation(request: CalculationRequest, x_api_key: str = Depends(verify_api_key)):
    # Check endpoint permission
    if not policy_engine.can_access_endpoint(x_api_key, "store_calculation"):
        raise HTTPException(status_code=403, detail="Service not authorized to store calculations")
    
    # Validate input values
    if not policy_engine.validate_calculation_input(x_api_key, request.num1, request.num2):
        raise HTTPException(status_code=400, detail="Input values exceed allowed range")
    
    # Store the request and result in MongoDB
    calculation = {
        "num1": request.num1,
        "num2": request.num2,
        "result": request.result
    }
    await collection.insert_one(calculation)
    
    return request

@app.get("/calculations", response_model=List[CalculationResponse])
async def get_calculations(x_api_key: str = Depends(verify_api_key)):
    # Check endpoint permission
    if not policy_engine.can_access_endpoint(x_api_key, "get_calculations"):
        raise HTTPException(status_code=403, detail="Service not authorized to read calculations")
    
    calculations = []
    async for calculation in collection.find():
        calculations.append(CalculationResponse(**calculation))
    return calculations