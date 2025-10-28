# Use Python 3.9 slim image as base (better compatibility)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=randwater_calculator.py
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Upgrade pip first to avoid hash checking issues
RUN pip install --upgrade pip && \
    pip install --no-cache-dir Flask==2.3.3 && \
    pip install --no-cache-dir WeasyPrint==60.2 && \
    pip install --no-cache-dir reportlab==4.0.4 && \
    pip install --no-cache-dir gunicorn==21.2.0 && \
    pip install --no-cache-dir pandas==2.1.4 && \
    pip install --no-cache-dir openpyxl==3.1.2 && \
    pip install --no-cache-dir requests==2.31.0 && \
    pip install --no-cache-dir Werkzeug==3.0.1

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p uploads backups drafts __pycache__ static/images

# Set permissions
RUN chmod +x run_randwater.py

# Expose port
EXPOSE 5001

# Command to run the application with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "randwater_calculator:app"]


