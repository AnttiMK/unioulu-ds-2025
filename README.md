# Distributed Calculator System

A comprehensive microservices-based distributed system featuring:

- FastAPI REST API with MongoDB persistence
- gRPC calculator service
- Kafka message streaming
- Prometheus and Grafana monitoring
- Policy-based access control
- TLS/SSL security
- Load testing with Locust


### Components:

1. **Calculator Client**: Sends random addition requests to the gRPC server
2. **Calculator Server (gRPC)**: Processes addition operations and publishes results to Kafka
3. **Kafka & ZooKeeper**: Message broker for asynchronous communication
4. **Calculator Consumer**: Reads calculation results from Kafka and forwards to FastAPI
5. **FastAPI Application**: REST API for storing and retrieving calculations
6. **MongoDB**: Database for persistent storage
7. **Policy Engine**: Enforces API access controls, rate limiting, and input validation
8. **Prometheus & Grafana**: For metrics collection and visualization
9. **Locust**: For load testing the system
10. **AI Agent**: OpenAI-powered evaluation service

## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [Docker + Docker Compose](https://docs.docker.com/compose/install/)

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the root directory:

```
CALCULATOR_CONSUMER_API_KEY=your_consumer_key_here
CALCULATOR_SERVER_API_KEY=your_server_key_here
```

### 2. Generate TLS Certificates

Run the certificate generation script:

```bash
python generate_certs.py
```

This will create self-signed certificates in the `certs` directory.

### 3. Setting up development environment

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Unix
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Building & running

```bash
docker compose up --build -d
```

## Accessing the Services

- **FastAPI**: https://localhost:8000 (HTTPS)
  - API Docs: https://localhost:8000/docs
- **MongoDB Express**: http://localhost:8081
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
  - Default credentials: admin/admin
  - Pre-configured dashboards for:
    - FastAPI metrics
    - gRPC metrics
    - Kafka metrics
    - Policy & admin metrics
- **Locust**: http://localhost:8089

## API Usage Examples

### REST API

```bash
# Store a calculation (authenticated)
curl -X POST https://localhost:8000/store_calculation \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_consumer_key_here" \
  -d '{"num1": 10, "num2": 20, "result": 30}' \
  --insecure

# Retrieve calculations (authenticated)
curl -X GET https://localhost:8000/calculations \
  -H "X-API-Key: your_consumer_key_here" \
  --insecure
```

### gRPC Service

The gRPC calculator service is accessible via port 50051 and automatically receives requests from the calculator client.

## Load Testing with Locust

Access the Locust web UI at http://localhost:8089 to configure and run load tests against the system.

## Additional Resources

- [gRPC Documentation](https://grpc.io/docs/languages/python/basics/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)