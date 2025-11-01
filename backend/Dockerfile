FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
# Use environment variable PORT if available, default to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
