# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for MySQL
RUN apt-get update && apt-get install -y gcc libmariadb-dev libmariadb-dev-compat && rm -rf /var/lib/apt/lists/*


# Copy requirements from backend and install dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/ /app

# Expose Flask and Prometheus ports
EXPOSE 5000 8000

# Run the Flask app
CMD ["python", "main.py"]
