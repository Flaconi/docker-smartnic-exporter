# Docker SmartNIC Exporter
Containerised Prometheus Smart-Nic Exporter


[![Docker Hub](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://hub.docker.com/r/flaconi/smartnic-exporter)
[![Build Status](https://img.shields.io/github/actions/workflow/status/Flaconi/docker-smartnic-exporter/docker_build.yml?label=build)](https://github.com/Flaconi/docker-smartnic-exporter/actions)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Prometheus Exporter](https://img.shields.io/badge/prometheus-exporter-orange)](https://prometheus.io/docs/instrumenting/exporters/)

## 📦 Overview

This Dockerized Python exporter collects domain data from the Smart-NIC SOAP API and writes Prometheus-compatible metrics to a `.prom` file. Designed for use with Prometheus `textfile` collector (e.g. via `node_exporter`).

---

## ⚙️ Features

- Fetches detailed domain data via SOAP
- Outputs `domain_info`, `domain_fetch_success`, `domain_fetch_timestamp`
- Labels include HTTP status, timestamp, and error messages
- Configurable via CLI args, env vars, or `.env` file
- Works with Prometheus `textfile` collector

---

## 🚀 Quickstart

### Option 1: Using `.env` file (recommended)

**.env**:
```env
EXPORT_USER=your-user
EXPORT_PASS=your-pass
EXPORT_INTERVAL=300
EXPORT_OUTPUT=/app/metrics/smartnic.prom
```

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/metrics:/app/metrics \
  docker.smartnic-exporter
```

---

### Option 2: Using CLI Arguments Only

```bash
docker run --rm \
  -v $(pwd)/metrics:/app/metrics \
  docker.smartnic-exporter \
  python exporter.py \
    --username your-user \
    --password your-pass \
    --interval 60 \
    --output /app/metrics/smartnic.prom
```

---

### Option 3: Using `-e` Environment Variables

```bash
docker run --rm \
  -e EXPORT_USER=your-user \
  -e EXPORT_PASS=your-pass \
  -e EXPORT_INTERVAL=120 \
  -e EXPORT_OUTPUT=/app/metrics/smartnic.prom \
  -v $(pwd)/metrics:/app/metrics \
  docker.smartnic-exporter
```

---

### Option 4: Mixed (override `.env` with CLI)

```bash
docker run --rm \
  --env-file .env \
  -e EXPORT_INTERVAL=60 \
  -v $(pwd)/metrics:/app/metrics \
  docker.smartnic-exporter \
  python exporter.py --output /app/metrics/custom.prom
```

> 🔄 Priority: CLI args > ENV vars > Defaults

---

## 🧪 Metrics Produced

### domain_info
```
domain_info{domain="...", reg_type="...", ...} 1
```
One per domain, with labels like owner, techC, nameservers, etc.

### domain_fetch_success
```
domain_fetch_success{timestamp="1718111200", status="success", code="200", error=""} 1
```
Indicates success (`1`) or failure (`0`).

### domain_fetch_timestamp
```
domain_fetch_timestamp{status="success", code="200", error=""} 1718111200
```
Last poll time with labels for status and HTTP code.

---

## 🔧 Docker Compose Example

```yaml
version: '3.8'

services:
  smartnic-exporter:
    image: docker.smartnic-exporter
    env_file: .env
    volumes:
      - ./metrics:/app/metrics
    restart: unless-stopped
```

---

## 📥 Build Image Locally

```bash
docker build -t docker.smartnic-exporter .
```

---

## 📂 Requirements

Install Python dependencies if running manually:
```text
requests
python-dotenv
```

Install:
```bash
pip install -r requirements.txt
```

---

## 🧯 Troubleshooting

- Ensure `.env` or env vars are valid
- Use `docker logs` to view error details
- If the fetch fails, the metrics file will still include labeled error state

---

## 💬 Questions or Improvements?
Feel free to contribute or open issues!
