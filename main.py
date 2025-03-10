from fastapi import FastAPI, Depends, Header, HTTPException  # FastAPI framework components
from pydantic import BaseModel, Field  # For data validation and schemas
from motor.motor_asyncio import AsyncIOMotorClient  # Async MongoDB driver
from typing import List, Optional  # Type hints
import os  # For environment variables
from prometheus_client import start_http_server, Summary, Counter, Gauge  # Prometheus metrics
from prometheus_client.exposition import generate_latest  # For exposing metrics
from fastapi.responses import PlainTextResponse  # For raw text responses
from prometheus_fastapi_instrumentator import Instrumentator  # Auto-instrumentation for FastAPI
from policy_engine import policy_engine  # Import the policy engine

# Initialize FastAPI app
app = FastAPI()

# Get MongoDB connection string from environment variable with fallback
mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:password@localhost:27017")

# Initialize Prometheus metrics server for FastAPI (8000)
Instrumentator().instrument(app).expose(app)  # Automatically instrument all FastAPI endpoints

# MongoDB connection
client = AsyncIOMotorClient(mongodb_url)  # Create async MongoDB client
db = client.calculations_db  # Select database
collection = db.calculations  # Select collection

# API key verification dependency using policy engine
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Dependency for verifying API keys in requests.
    
    This function checks if the API key is present, valid, and not rate-limited.
    It's used as a dependency in FastAPI route handlers.
    
    Args:
        x_api_key: The API key from the X-API-Key header
        
    Returns:
        The valid API key
        
    Raises:
        HTTPException: If API key is missing, invalid, or rate limited
    """
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="API Key is missing")
    
    if not policy_engine.is_valid_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    if not policy_engine.check_rate_limit(x_api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return x_api_key

@app.get("/")
async def read_root():
    """Simple root endpoint that returns a welcome message"""
    return {"message": "Hello, FastAPI and MongoDB!"}

# Pydantic models for request/response validation
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
    """
    Endpoint to store calculation results in MongoDB.
    
    This endpoint validates permissions and input values before storing the calculation.
    
    Args:
        request: The calculation data from the request body
        x_api_key: The validated API key from the verify_api_key dependency
        
    Returns:
        The stored calculation data
        
    Raises:
        HTTPException: If service is not authorized or input values exceed allowed ranges
    """
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
    await collection.insert_one(calculation)  # Async insert into MongoDB
    
    return request  # Return the request object as the response

@app.get("/calculations", response_model=List[CalculationResponse])
async def get_calculations(x_api_key: str = Depends(verify_api_key)):
    """
    Endpoint to retrieve all stored calculations.
    
    Args:
        x_api_key: The validated API key from the verify_api_key dependency
        
    Returns:
        A list of all calculation records in the database
        
    Raises:
        HTTPException: If service is not authorized to read calculations
    """
    # Check endpoint permission
    if not policy_engine.can_access_endpoint(x_api_key, "get_calculations"):
        raise HTTPException(status_code=403, detail="Service not authorized to read calculations")
    
    calculations = []
    # Async iteration through MongoDB results
    async for calculation in collection.find():
        calculations.append(CalculationResponse(**calculation))  # Convert to Pydantic model
    return calculations

if __name__ == "__main__":
    import uvicorn
    # Start the ASGI server with HTTPS support
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        ssl_keyfile="/app/certs/key.pem",  # Path to SSL key
        ssl_certfile="/app/certs/cert.pem"  # Path to SSL certificate
    )