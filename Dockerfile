FROM python:3.10-slim

WORKDIR /app

# Upgrade pip and install standard build dependencies (in case mysqlclient needs it)
RUN apt-get update \
    && apt-get install -y default-libmysqlclient-dev build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Environment
ENV FLASK_APP=app.main:create_app
ENV PYTHONPATH=/app

# Expose Gunicorn HTTP Port
EXPOSE 5000

# Run via standard WSGI Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:create_app()"]
