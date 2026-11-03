FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && useradd --uid 10001 --create-home scheduler \
    && mkdir -p /state \
    && chown 10001:10001 /state
COPY worker.py /app/worker.py

VOLUME ["/state"]
USER 10001:10001
ENTRYPOINT ["python", "/app/worker.py"]
