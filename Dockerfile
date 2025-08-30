FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variable default
ENV PORT=5000

# Use the railway app with explicit Python
CMD ["python", "railway_app.py"]