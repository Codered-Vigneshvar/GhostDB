FROM python:3.11-slim

WORKDIR /app

# Ensure we have the base build tools and curl for anything internal
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir setuptools wheel

# Install dependencies using standard approach
COPY pyproject.toml /app/
RUN pip install --no-cache-dir .

# Copy environment code
COPY . /app

EXPOSE 8000

# Execute FastAPI via Uvicorn from openenv specs
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
