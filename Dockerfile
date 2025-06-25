FROM python:3.11-slim

WORKDIR /app

COPY exporter.py .

RUN pip install requests python-dotenv

CMD ["python", "exporter.py"]
