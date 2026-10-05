# Trigonometry Visualizer - Flask application image (Req 5.1)
FROM python:3.12-slim

# Keep Python output unbuffered and skip .pyc files for cleaner container logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the application source
COPY . .

# Flask app listens on 5000 (matches app.py app.run default)
EXPOSE 5000

# Serve the WSGI app (app:app) with gunicorn on port 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
