FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY="your-secure-production-key-should-be-set-at-runtime"
ENV MONGO_URI="mongodb://mongo:27017"
ENV MONGO_DB_NAME="cesizen_auth"
ENV ADMIN_USERNAME="admin"
ENV ADMIN_PASSWORD="admin"
ENV ADMIN_EMAIL="admin@example.com"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose API port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]