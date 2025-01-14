# Use a base image with Python 3.9-slim
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy FastAPI app files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 5508

# Start Streamlit app
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=5508"]
