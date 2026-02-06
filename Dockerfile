# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# MongoDB connection string (user key)
# Override this in Render's Environment tab with your real URI
ENV MONGO_URI="mongodb+srv://sree71816_db_user:NO5jq7RLo7dhcZHN@cluster0.gbttwr6.mongodb.net/business_card_db?retryWrites=true&w=majority"

# Install system dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p uploads

# Expose port
EXPOSE 10000

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "app:app"]