ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY exporter.py .


CMD ["python", "exporter.py"]
