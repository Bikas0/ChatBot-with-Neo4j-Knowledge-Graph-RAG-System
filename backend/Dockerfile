# Use a base image with Python 3.9-slim
FROM python:3.9-slim

# Install system dependencies for libmagic
RUN apt-get update && apt-get install -y libmagic1

# Set working directory
WORKDIR /app

# Copy FastAPI app files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5507

# Start FastAPI app with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5507"]
