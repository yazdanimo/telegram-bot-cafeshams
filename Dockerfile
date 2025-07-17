# Use Python 3.11 official image
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8443

# جایگزین کردن Flask dev server با Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8443", "--timeout", "120", "--workers", "1", "--threads", "2", "main:flask_app"]
