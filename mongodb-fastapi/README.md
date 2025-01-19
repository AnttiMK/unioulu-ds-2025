# FastAPI + MongoDB with Docker Compose

## Prerequisites
- [Python 3.13+](https://www.python.org/downloads/)
- [Docker + Docker Compose](https://docs.docker.com/compose/install/)

## Setting up development environment
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Unix
source .venv/bin/activate

pip install -r requirements.txt
```

## Building & running
Container can be built and run by running Docker Compose:
```bash
docker compose up --build -d
```
FastAPI will be accessible at http://localhost:8000, and mongo-express can be found at http://localhost:8081.  
To rebuild the container, just run the above command again.

## Example HTTP request
`POST http://localhost:8000/store_calculation`
```json
{
    "num1": 1,
    "num2": 2,
    "result": 3
}
```