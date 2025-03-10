from fastapi import FastAPI, HTTPException  # FastAPI framework for building APIs
from pydantic import BaseModel  # For data validation and parsing
from openai import OpenAI  # OpenAI Python client library
import uvicorn  # ASGI server for running FastAPI applications

# Note: For the sake of privacy, the API key is stored in a file called apikey.txt
# The file is not uploaded to the repository

# Read the API key from a file
with open('apikey.txt', 'r') as file:
    data = file.read().rstrip()  # Remove any trailing whitespace

# Set your API key for OpenAI
openai_api_key = data

# Initialize the OpenAI client with the API key
client = OpenAI(
    api_key=openai_api_key,  # This is the default and can be omitted
)

# Initialize FastAPI application
app = FastAPI()

# Define the data model for user requests
class UserInput(BaseModel):
    user_input: str  # The input string from the user (login attempt details)

@app.post("/generate_response/")
def generate_response(user_input: UserInput):
    """
    Generates a response from OpenAI's GPT model using prompt engineering.
    
    This endpoint receives login attempt data and evaluates whether it's suspicious
    by comparing it to user's historical patterns using AI.
    
    Args:
        user_input: A UserInput object containing the user's input string
        
    Returns:
        A JSON response with the AI's assessment ("NORMAL" or "SUSPICIOUS: [Explanation]")
    """
    # Construct the prompt with system instructions and user input
    messages = [
        {"role": "system", "content":
            """You are a cybersecurity expert in charge of flagging anomalous login attempts as suspicious.
            Compare the login attempts to the user's historical data. 
            If the attempt is anomalous compared to the data, return a detailed explanation why in the following format:
            SUSPICIOUS: [Explanation]
            If the attempt is normal, return: NORMAL."""},
        {"role": "user", "content": user_input.user_input}  # Add the user's input to the messages
    ]
    
    # Make API call to OpenAI's GPT model
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Specify which GPT model to use
        messages=messages,  # The prompt built above
        temperature=0.7,  # Controls randomness (0=deterministic, 1=very random)
        max_tokens=200,  # Maximum response length
        top_p=1.0,  # Alternative to temperature for controlling randomness
        frequency_penalty=0.5,  # Reduce repetition of similar phrases
        presence_penalty=0.3  # Encourage the model to talk about new topics
    )

    # Extract and return just the text content from the response
    return {"response": response.choices[0].message.content}

# Run the server when the script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)  # Start server on all interfaces, port 8005