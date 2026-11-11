FROM docker.io/library/python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY start.sh .
RUN chmod +x start.sh

RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown appuser:appuser /app/data

ENV DATABASE_URL=sqlite:////app/data/pokemon.db

USER appuser

EXPOSE 8000

CMD ["./start.sh"]