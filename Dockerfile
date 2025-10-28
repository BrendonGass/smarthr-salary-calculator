# Use Python 3.9 slim image as base (better compatibility)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=randwater_calculator.py
ENV FLASK_ENV=production

# Install system dependencies including WeasyPrint requirements
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-liberation \
    curl \
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

# Create necessary directories and initialize JSON files
# Remove any existing directories that should be files
RUN mkdir -p uploads backups drafts __pycache__ static/images && \
    rm -rf employee_access.json employee_packages.json randwater_package_audit.json \
           submitted_packages.json sap_uploads.json system_logs.json system_users.json \
           password_reset_tokens.json randwater_notifications.json email_logs.json \
           package_audit.json salary_simulations.json randwater_data.db && \
    echo '{}' > employee_access.json && \
    echo '{}' > employee_packages.json && \
    echo '[]' > randwater_package_audit.json && \
    echo '[]' > submitted_packages.json && \
    echo '[]' > sap_uploads.json && \
    echo '[]' > system_logs.json && \
    echo '[]' > system_users.json && \
    echo '{}' > password_reset_tokens.json && \
    echo '[]' > randwater_notifications.json && \
    echo '[]' > email_logs.json && \
    echo '[]' > package_audit.json && \
    echo '[]' > salary_simulations.json

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh run_randwater.py

# Expose port
EXPOSE 5002

# Use entrypoint for initialization
ENTRYPOINT ["/docker-entrypoint.sh"]

# Command to run the application with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "randwater_calculator:app"]


