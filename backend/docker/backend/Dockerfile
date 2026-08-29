FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/evmbench
WORKDIR /opt/evmbench

RUN pip install --no-cache-dir uv

RUN uv pip install --system --no-cache \
        fastapi "uvicorn[standard]" python-multipart \
        "psycopg[binary,pool]" pydantic-settings docker httpx cryptography pika

COPY backend/ ./backend/

RUN useradd --uid 10002 --create-home service
USER service

#   api        uvicorn backend.api.main:app   --host 0.0.0.0 --port 1337
#   proxy      uvicorn backend.proxy.main:app --host 0.0.0.0 --port 8084
#   instancer  python -m backend.instancer.consumer
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "1337"]
