from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import uvicorn

# Note: For the sake of privacy, the API key is stored in a file called apikey.txt
# The file is not uploaded to the repository

# Read the API key from a file
with open('apikey.txt', 'r') as file:
    data = file.read().rstrip()

# Set your API key
openai_api_key = data

client = OpenAI(
    api_key=openai_api_key,  # This is the default and can be omitted
)

app = FastAPI()

class UserInput(BaseModel):
    user_input: str

@app.post("/generate_response/")
def generate_response(user_input: UserInput):
    """
    Generates a response from OpenAI's GPT model using prompt engineering.
    """
    messages = [
        {"role": "system", "content":
            """You are a cybersecurity expert in charge of flagging anomalous login attempts as suspicious.
            Compare the login attempts to the user's historical data. 
            If the attempt is anomalous compared to the data, return a detailed explanation why in the following format:
            SUSPICIOUS: [Explanation]
            If the attempt is normal, return: NORMAL."""},
        {"role": "user", "content": user_input.user_input}
    ]
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use "gpt-3.5-turbo" if needed
        messages=messages,
        temperature=0.7,
        max_tokens=200,
        top_p=1.0,
        frequency_penalty=0.5,
        presence_penalty=0.3
    )

    # Correct way to extract content
    return {"response": response.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
