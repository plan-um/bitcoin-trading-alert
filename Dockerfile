FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway will provide PORT env var, but we ignore it
EXPOSE 8080

# Run directly with Python
CMD ["python", "main.py"]