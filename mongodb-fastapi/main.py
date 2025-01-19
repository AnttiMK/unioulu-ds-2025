from fastapi import FastAPI
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
import os

app = FastAPI()

mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:password@localhost:27017")

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
