FROM python:3.11-slim

# Ish papkasi
WORKDIR /app

# Tizim paketlari
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python paketlari
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod
COPY src/ ./src/
COPY pyproject.toml .

# Media papkasi
RUN mkdir -p /app/media /app/logs

# Non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Entry point
CMD ["python", "-m", "src.main"]

