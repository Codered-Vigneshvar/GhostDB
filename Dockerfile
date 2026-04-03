FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir setuptools wheel

COPY pyproject.toml /app/
RUN pip install --no-cache-dir .

COPY . /app

EXPOSE 8000

# Execute FastAPI via Uvicorn from the new ghost_query package
CMD ["uvicorn", "ghost_query.app:app", "--host", "0.0.0.0", "--port", "8000"]
