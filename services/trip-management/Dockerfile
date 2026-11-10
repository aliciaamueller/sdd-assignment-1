# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

# Dependencies before source, so editing code does not reinstall packages.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Source files are listed one by one: no COPY . ., so .env and local
# databases can never reach the image.
COPY app.py ./

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --access-logfile - app:app"]
