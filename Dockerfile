FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY --from=builder /install /usr/local
COPY . .

RUN chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120", "main:app"]
