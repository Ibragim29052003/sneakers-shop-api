FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system app && adduser --system --ingroup app app
COPY --chown=app:app . /app
RUN mkdir -p /app/media /app/staticfiles && chown -R app:app /app

USER app

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
