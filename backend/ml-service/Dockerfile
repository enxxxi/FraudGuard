# Use official lightweight Python 3.10 image to support Union type hints (|)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY fraud_model.pkl .
COPY feature_columns.pkl .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app with Uvicorn, respecting PORT env var
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
