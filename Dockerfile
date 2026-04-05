# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for FastAPI
EXPOSE 8000

# Start server
CMD ["uvicorn", "ghost_query.api.openenv_app:app", "--host", "0.0.0.0", "--port", "8000"]
