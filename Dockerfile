FROM python:3.11-slim

WORKDIR /app

COPY pipeline /app/pipeline
COPY api /app/api
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/app

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]