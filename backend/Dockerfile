FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.runtime.lock.txt /app/requirements.runtime.lock.txt

RUN python -m pip install \
    --no-cache-dir \
    -r /app/requirements.runtime.lock.txt

RUN useradd \
    --create-home \
    --uid 10001 \
    appuser

COPY --chown=appuser:appuser backend /app/backend

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
