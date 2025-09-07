# Travel Planner Agent - Docker Deployment Guide

This guide explains how to deploy the Travel Planner Agent using Docker, similar to your PhotoBook service.

## Files Created

- `Dockerfile` - Container definition
- `startup.sh` - Application startup script
- `test_startup.py` - Startup validation tests
- `docker-compose.yml` - Local development setup
- `.dockerignore` - Build optimization

## Prerequisites

1. **Docker installed** on your system
2. **Environment variables** configured (see below)
3. **API keys** for required services

## Required Environment Variables

```bash
GEMINI_API_KEY=your_gemini_api_key
APIFY_API_TOKEN=your_apify_token
SERPER_API_KEY=your_serper_key
HF_TOKEN=your_huggingface_token  # Optional
```

## Local Development

### Using Docker Compose (Recommended)

1. Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your_gemini_api_key
APIFY_API_TOKEN=your_apify_token
SERPER_API_KEY=your_serper_key
HF_TOKEN=your_huggingface_token
```

2. Build and run:
```bash
docker-compose up --build
```

3. Access the application at `http://localhost:8080`

### Using Docker Commands

1. Build the image:
```bash
docker build -t travel-planner-agent .
```

2. Run the container:
```bash
docker run -p 8080:8080 \
  -e GEMINI_API_KEY=your_key \
  -e APIFY_API_TOKEN=your_token \
  -e SERPER_API_KEY=your_key \
  travel-planner-agent
```

## Google Cloud Platform Deployment

### Cloud Run Deployment

1. **Build and push to Google Container Registry:**
```bash
# Set your project ID
export PROJECT_ID=your-gcp-project-id

# Build and tag the image
docker build -t gcr.io/$PROJECT_ID/travel-planner-agent .

# Push to GCR
docker push gcr.io/$PROJECT_ID/travel-planner-agent
```

2. **Deploy to Cloud Run:**
```bash
gcloud run deploy travel-planner-agent \
  --image gcr.io/$PROJECT_ID/travel-planner-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PYTHONUNBUFFERED=1 \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --concurrency 80
```

3. **Set environment variables:**
```bash
gcloud run services update travel-planner-agent \
  --set-env-vars GEMINI_API_KEY=your_key,APIFY_API_TOKEN=your_token,SERPER_API_KEY=your_key \
  --region us-central1
```

### Alternative: Cloud Build + Cloud Run

Create `cloudbuild.yaml`:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/travel-planner-agent', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/travel-planner-agent']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'travel-planner-agent'
      - '--image'
      - 'gcr.io/$PROJECT_ID/travel-planner-agent'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
```

## API Endpoints

- **POST /travel** - Process travel planning queries
- **GET /health** - Health check endpoint

## Example Usage

```bash
# Health check
curl http://localhost:8080/health

# Travel planning request
curl -X POST http://localhost:8080/travel \
  -H "Content-Type: application/json" \
  -d '{"query": "Plan a 5-day trip to Europe for 2 people"}'
```

## Monitoring and Logs

- Health checks run every 60 seconds
- Application logs are available via `docker logs` or Cloud Run logs
- Startup tests validate all dependencies before serving traffic

## Security Features

- Runs as non-root user (appuser)
- Minimal base image (python:3.9-slim)
- Environment variable injection for secrets
- Health checks for reliability

## Troubleshooting

1. **Startup failures**: Check logs for missing environment variables
2. **Import errors**: Verify all dependencies in requirements.txt
3. **Memory issues**: Increase memory allocation in Cloud Run
4. **Timeout issues**: Adjust timeout settings for long-running requests

## Resource Requirements

- **Memory**: 1GB recommended (minimum 512MB)
- **CPU**: 1 vCPU recommended
- **Storage**: Minimal (image ~500MB)
- **Port**: 8080 (configurable via PORT env var)
