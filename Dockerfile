FROM python:3.11-slim

WORKDIR /app

COPY pipeline /app/pipeline
COPY ui /app/ui
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e .


ENV PYTHONPATH=/app

CMD ["streamlit", "run", "ui/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]