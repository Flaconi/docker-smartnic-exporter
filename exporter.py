import os
import time
import argparse
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import logging
import sys

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logging.info("Metrics script started.")

# load .env
load_dotenv()


def prom_escape(value):
    return str(value or "").replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def get_config_value(arg_value, env_var_name, default=None, required=False, cast=str):
    if arg_value is not None:
        source = "argument"
        value = arg_value
    elif os.getenv(env_var_name) is not None:
        source = "env"
        value = os.getenv(env_var_name)
    else:
        source = "default"
        value = default

    if required and not value:
        logging.error(f"Missing required config value: {env_var_name}")
        sys.exit(1)

    try:
        value = cast(value)
    except Exception as e:
        logging.error(f"Could not convert value '{value}' for '{env_var_name}' to {cast.__name__}: {e}")
        sys.exit(1)

    return value, source


def load_soap_body(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def fetch_and_write_metrics(soap_file_path, username, password, parser_fn):
    url = "https://soap.domain-bestellsystem.de/soap.php"
    soap_body = load_soap_body(soap_file_path)

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": ""
    }

    metrics = []
    status = "error"
    error_msg = ""
    status_code = 0

    try:
        response = requests.post(
            url,
            data=soap_body,
            headers=headers,
            auth=HTTPBasicAuth(username, password),
            timeout=60,
        )
        status_code = response.status_code

        if response.status_code != 200:
            error_msg = f"Unexpected response. Status code: {response.status_code}, Response Text: {response.text}"
            logging.error(error_msg)
        else:
            metrics.extend(parser_fn(response.text))
            status = "success"

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Exception during fetch: {error_msg}")

    timestamp = int(time.time())

    return metrics, {
        "status": status,
        "code": status_code,
        "error": error_msg,
        "timestamp": timestamp,
        "source": parser_fn.__name__,
    }


def parse_domain_response(xml_text):
    root = ET.fromstring(xml_text)
    metrics = []

    for elem in root.iter():
        if elem.tag.endswith('domainInfoItem'):
            domain_data = {}
            for item in elem.findall('./item'):
                key_elem = item.find('./key')
                value_elem = item.find('./value')
                if key_elem is not None and value_elem is not None:
                    domain_data[key_elem.text] = value_elem.text

            if "domainName" in domain_data:
                metric_line = (
                    f'domain_info{{'
                    f'domain="{prom_escape(domain_data.get("domainName", ""))}", '
                    f'reg_type="{prom_escape(domain_data.get("regType", ""))}", '
                    f'reseller="{prom_escape(domain_data.get("reseller", ""))}", '
                    f'adminC="{prom_escape(domain_data.get("adminC", ""))}", '
                    f'ownerC="{prom_escape(domain_data.get("ownerC", ""))}", '
                    f'techC="{prom_escape(domain_data.get("techC", ""))}", '
                    f'zoneC="{prom_escape(domain_data.get("zoneC", ""))}", '
                    f'nameserver="{prom_escape(domain_data.get("nameserver", ""))}", '
                    f'status="{prom_escape(domain_data.get("status", ""))}", '
                    f'domainStatus="{prom_escape(domain_data.get("domainStatus", ""))}", '
                    f'regStatus="{prom_escape(domain_data.get("regStatus", ""))}", '
                    f'systemInDate="{prom_escape(domain_data.get("systemInDate", ""))}", '
                    f'orderDate="{prom_escape(domain_data.get("orderDate", ""))}", '
                    f'orderNumber="{prom_escape(domain_data.get("orderNumber", ""))}", '
                    f'toBeDeletedDate="{prom_escape(domain_data.get("toBeDeletedDate", ""))}", '
                    f'trusteeWPP="{prom_escape(domain_data.get("trusteeWPP", ""))}", '
                    f'irtpStatus="{prom_escape(domain_data.get("irtpStatus", ""))}"'
                    f'}} 1'
                )
                metrics.append(metric_line)

    return metrics


def ssl_labels(cert_data):
    return (
        f'domain="{prom_escape(cert_data.get("domain", ""))}", '
        f'orderNumber="{prom_escape(cert_data.get("orderNumber", ""))}", '
        f'reseller="{prom_escape(cert_data.get("reseller", ""))}", '
        f'status="{prom_escape(cert_data.get("status", ""))}", '
        f'software="{prom_escape(cert_data.get("software", ""))}", '
        f'productId="{prom_escape(cert_data.get("productId", ""))}", '
        f'valid_from="{prom_escape(cert_data.get("notValidBefore", "0"))}", '
        f'valid_to="{prom_escape(cert_data.get("notValidAfter", "0"))}"'
    )


def parse_ssl_response(xml_text):
    root = ET.fromstring(xml_text)
    now = int(time.time())

    info_metrics = []
    valid_from_metrics = []
    valid_to_metrics = []
    days_remaining_metrics = []

    for elem in root.iter():
        if elem.tag.endswith('item'):
            xsi_type = elem.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}type', '')
            if not xsi_type.endswith('SslInfo'):
                continue

            cert_data = {}
            for child in elem:
                tag = child.tag.split('}')[-1]
                cert_data[tag] = child.text or ""

            domain = cert_data.get("domain", "")
            if not domain:
                continue

            not_before = cert_data.get("notValidBefore", "0")
            not_after = cert_data.get("notValidAfter", "0")
            labels = ssl_labels(cert_data)

            try:
                not_before_int = int(not_before)
                not_after_int = int(not_after)
            except ValueError:
                not_before_int = 0
                not_after_int = 0

            info_metrics.append(f"ssl_cert_info{{{labels}}} 1")

            if not_before_int:
                valid_from_metrics.append(
                    f"ssl_cert_valid_not_before{{{labels}}} {not_before_int}"
                )
            if not_after_int:
                valid_to_metrics.append(
                    f"ssl_cert_valid_not_after{{{labels}}} {not_after_int}"
                )
                days_remaining_metrics.append(
                    f"ssl_cert_days_remaining{{{labels}}} {(not_after_int - now) // 86400}"
                )

    return [
        "# HELP ssl_cert_info SSL certificate details",
        "# TYPE ssl_cert_info gauge",
        *info_metrics,
        "# HELP ssl_cert_valid_not_before Not valid before timestamp",
        "# TYPE ssl_cert_valid_not_before gauge",
        *valid_from_metrics,
        "# HELP ssl_cert_valid_not_after Not valid after timestamp",
        "# TYPE ssl_cert_valid_not_after gauge",
        *valid_to_metrics,
        "# HELP ssl_cert_days_remaining Days until expiry",
        "# TYPE ssl_cert_days_remaining gauge",
        *days_remaining_metrics,
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, help="Interval in Seconds (Default: EXPORT_INTERVAL)")
    parser.add_argument("--output", help="Path for metrics (Default: EXPORT_OUTPUT)")
    parser.add_argument("--username", help="Username (Default: EXPORT_USER)")
    parser.add_argument("--password", help="Password (Default: EXPORT_PASS)")
    args = parser.parse_args()

    interval, _ = get_config_value(args.interval, "EXPORT_INTERVAL", default=300, cast=int)
    output, _ = get_config_value(args.output, "EXPORT_OUTPUT", default="metrics/ext_metrics.prom")
    username, _ = get_config_value(args.username, "EXPORT_USER", required=True)
    password, _ = get_config_value(args.password, "EXPORT_PASS", required=True)

    while True:
        all_metrics = []

        all_metrics.append("# HELP domain_info Domain state with extra labels")
        all_metrics.append("# TYPE domain_info gauge")
        domain_metrics, domain_status = fetch_and_write_metrics("soap_bodies/domain_request.xml", username, password, parse_domain_response)
        all_metrics += domain_metrics

        all_metrics.append("# HELP domain_fetch_success Was the last fetch successful (1) or not (0)")
        all_metrics.append("# TYPE domain_fetch_success gauge")
        all_metrics.append(
            f'domain_fetch_success{{timestamp="{domain_status["timestamp"]}", status="{prom_escape(domain_status["status"])}", code="{domain_status["code"]}", error="{prom_escape(domain_status["error"])}", source="{prom_escape(domain_status["source"])}"}} {1 if domain_status["status"] == "success" else 0}'
        )
        all_metrics.append("# HELP domain_fetch_timestamp Unix timestamp of last fetch attempt")
        all_metrics.append("# TYPE domain_fetch_timestamp gauge")
        all_metrics.append(
            f'domain_fetch_timestamp{{status="{prom_escape(domain_status["status"])}", code="{domain_status["code"]}", error="{prom_escape(domain_status["error"])}", source="{prom_escape(domain_status["source"])}"}} {domain_status["timestamp"]}'
        )

        ssl_metrics, ssl_status = fetch_and_write_metrics("soap_bodies/ssl_request.xml", username, password, parse_ssl_response)
        all_metrics += ssl_metrics

        all_metrics.append("# HELP ssl_fetch_success Was the last fetch successful (1) or not (0)")
        all_metrics.append("# TYPE ssl_fetch_success gauge")
        all_metrics.append(
            f'ssl_fetch_success{{timestamp="{ssl_status["timestamp"]}", status="{prom_escape(ssl_status["status"])}", code="{ssl_status["code"]}", error="{prom_escape(ssl_status["error"])}", source="{prom_escape(ssl_status["source"])}"}} {1 if ssl_status["status"] == "success" else 0}'
        )
        all_metrics.append("# HELP ssl_fetch_timestamp Unix timestamp of last fetch attempt")
        all_metrics.append("# TYPE ssl_fetch_timestamp gauge")
        all_metrics.append(
            f'ssl_fetch_timestamp{{status="{prom_escape(ssl_status["status"])}", code="{ssl_status["code"]}", error="{prom_escape(ssl_status["error"])}", source="{prom_escape(ssl_status["source"])}"}} {ssl_status["timestamp"]}'
        )

        output_dir = os.path.dirname(output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        tmp_output = f"{output}.tmp"
        with open(tmp_output, "w", encoding="utf-8") as f:
            for line in all_metrics:
                f.write(f"{line}\n")

        os.replace(tmp_output, output)

        logging.info(f"Wrote {len(all_metrics)} combined metrics to {output}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
