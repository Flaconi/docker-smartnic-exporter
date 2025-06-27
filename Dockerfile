ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION}

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy exporter and SOAP body files
COPY exporter.py .
COPY soap_bodies ./soap_bodies

CMD ["python", "exporter.py"]
