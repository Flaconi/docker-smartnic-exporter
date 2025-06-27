# Docker SmartNIC Exporter
Containerized exporter that fetches domain and SSL certificate data from the [Smart-NIC SOAP API](https://www.smart-nic.de/) and exposes Prometheus-compatible metrics via textfile format.

[![Docker Hub](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://hub.docker.com/r/flaconi/smartnic-exporter)
[![Build Status](https://img.shields.io/github/actions/workflow/status/Flaconi/docker-smartnic-exporter/docker_build.yml?label=build)](https://github.com/Flaconi/docker-smartnic-exporter/actions)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Prometheus Exporter](https://img.shields.io/badge/prometheus-exporter-orange)](https://prometheus.io/docs/instrumenting/exporters/)

---

## 📚 Table of Contents

- [📦 Overview](#-overview)
- [⚙️ Features](#-features)
- [🚀 Quickstart](#-quickstart)
- [📂 Project Structure](#-project-structure)
- [📊 Metrics](#-metrics)
- [🔧 Docker Compose Example](#-docker-compose-example)
- [📥 Build Image Locally](#-build-image-locally)
- [🧯 Troubleshooting](#-troubleshooting)
- [💬 Feedback & Contributions](#-feedback--contributions)

---

## 📦 Overview

This Dockerized Python exporter collects domain data from the Smart-NIC SOAP API and writes Prometheus-compatible metrics to a `.prom` file. Designed for use with Prometheus `textfile` collector (e.g. via `node_exporter`).

---

## ⚙️ Features

- Fetches:
  - Domain info
  - SSL certificate details
- Exposes:
  - Domain lifecycle status and metadata
  - SSL certificate validity dates and days until expiration
- Includes fetch diagnostics (`success`, `error`, `timestamp`)
- Fully configurable via:
  - CLI args
  - Environment variables
  - `.env` file
- Compatible with Docker and Docker Compose

---

## 🚀 Quickstart

### 🔐 Using `.env` file (recommended)

**.env**
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
  flaconi/smartnic-exporter
```

### 🖥 Using CLI arguments

```bash
docker run --rm \
  -v $(pwd)/metrics:/app/metrics \
  flaconi/smartnic-exporter \
  python exporter.py \
    --username your-user \
    --password your-pass \
    --interval 60 \
    --output /app/metrics/smartnic.prom
```

### 🧪 Environment variables directly

```bash
docker run --rm \
  -e EXPORT_USER=your-user \
  -e EXPORT_PASS=your-pass \
  -e EXPORT_INTERVAL=120 \
  -e EXPORT_OUTPUT=/app/metrics/smartnic.prom \
  -v $(pwd)/metrics:/app/metrics \
  flaconi/smartnic-exporter```
````

### 🔁 Mixed (env + CLI override)

```bash
docker run --rm \
  --env-file .env \
  -e EXPORT_INTERVAL=60 \
  -v $(pwd)/metrics:/app/metrics \
  flaconi/smartnic-exporter \
  python exporter.py --output /app/metrics/custom.prom
```

> ⏱️ **Priority:** CLI args > ENV vars > `.env` > Defaults

---

## 📂 Project Structure

```text
smartnic-exporter/
├── docker-compose.yml
├── .env                      # Configuration (see Quickstart)
├── metrics/                  # Prometheus .prom output (mounted)
│   └── smartnic.prom
├── soap_bodies/              # SOAP XML requests (mounted or baked into image)
│   ├── domain_request.xml
│   └── ssl_request.xml
├── exporter.py               # Main exporter script
├── requirements.txt          # Python dependencies
└── Dockerfile
```

> ℹ️ The exporter reads SOAP requests from `soap_bodies/domain_request.xml` and `soap_bodies/ssl_request.xml`.  
> These files can be:
> - ✅ Mounted at runtime (**recommended** for easy customization)
> - 📦 Or baked into the Docker image (see `Dockerfile`)

---

## 📨 SOAP Request Templates

The `soap_bodies/` folder contains XML request templates used to query the [SmartNIC SOAP API](https://www.smart-nic.de/).

- `domain_request.xml` — Fetches domain metadata
- `ssl_request.xml` — Fetches SSL certificate information

You can modify these templates to apply filters (e.g. by `reseller`, `domain`, etc.) or adjust the fields you want to retrieve.

---

## 📊 Metrics

Note: Each fetch (domain and SSL) generates its own `fetch_success` and `fetch_timestamp` metrics.  
These include a `source="parse_domain_response"` or `source="parse_ssl_response"` label for context.


### 🏷️ `domain_info`
```text
domain_info{domain="example.de", reg_type="external", reseller="reseller-123", ...} 1
```

### ✅ `domain_fetch_success`
```text
domain_fetch_success{timestamp="1718111200", status="success", code="200", error=""} 1
```

### 🕓 `domain_fetch_timestamp`
```text
domain_fetch_timestamp{status="success", code="200", error=""} 1718111200
```

### 🔐 `ssl_cert_info`
```text
ssl_cert_info{domain="*.example.net", orderNumber="1337", reseller="reseller-123", status="ssl_ok", productId="SSL-80", valid_from="1746576000", valid_to="1780876799"} 1
```

### 📅 `ssl_cert_valid_not_before`
```text
ssl_cert_valid_not_before{domain="*.example.net"} 1746576000
```

### 📅 `ssl_cert_valid_not_after`
```text
ssl_cert_valid_not_after{domain="*.example.net"} 1780876799
```

### ⏳ `ssl_cert_days_remaining`
```text
ssl_cert_days_remaining{domain="*.example.net"} 346
```

---

## 🔧 Docker Compose Example

```yaml
version: '3.8'
services:
  smartnic-exporter:
    image: flaconi/smartnic-exporter
    env_file: .env
    volumes:
      - ./metrics:/app/metrics
    restart: unless-stopped
```

---

## 📥 Build Image Locally

```bash
git clone https://github.com/Flaconi/docker-smartnic-exporter
cd docker-smartnic-exporter

# install dependencies
pip install -r requirements.txt

# run the exporter
python exporter.py --username foo --password bar --output metrics/smartnic.prom
```

---

## 🧯 Troubleshooting

- Check `docker logs` for errors or HTTP failures
- Even on failure, metrics are written with error details
- Validate `.env` syntax (no quotes needed for strings)
- Verify SmartNIC credentials and API access
- Ensure file output path is writeable by the container

---

## 💬 Feedback & Contributions

Feel free to open issues, suggest improvements, or submit PRs.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
