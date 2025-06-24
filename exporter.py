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

def fetch_and_write_metrics(output_file, username, password):
    url = "https://soap.domain-bestellsystem.de/soap.php"

    soap_body = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                      xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                      xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:ns="http://soap.domain-bestellsystem.de/soap/1.1/">
       <soapenv:Header/>
       <soapenv:Body>
          <ns:domainListExtended soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
             <domainListExtendedRequest xsi:type="ns:DomainListExtendedRequestObject">
                <level xsi:type="xsd:string">own</level>
                <limit xsi:type="xsd:string">300</limit>
                <offset xsi:type="xsd:string">0</offset>
                <filter xsi:type="ns:ArrayOfFilteritem">
                   <item xsi:type="ns:FilterItem">
                      <key xsi:type="xsd:string"></key>
                      <value xsi:type="xsd:string"></value>
                   </item>
                </filter>
                <fields xsi:type="ns:ArrayOfString">
                   <item xsi:type="xsd:string">domainName</item>
                   <item xsi:type="xsd:string">domainStatus</item>
                   <item xsi:type="xsd:string">regType</item>
                   <item xsi:type="xsd:string">reseller</item>
                   <item xsi:type="xsd:string">irtpStatus</item>
                   <item xsi:type="xsd:string">adminC</item>
                   <item xsi:type="xsd:string">ownerC</item>
                   <item xsi:type="xsd:string">zoneC</item>
                   <item xsi:type="xsd:string">techC</item>
                   <item xsi:type="xsd:string">nameserver</item>
                   <item xsi:type="xsd:string">systemInDate</item>
                   <item xsi:type="xsd:string">orderDate</item>
                   <item xsi:type="xsd:string">orderNumber</item>
                   <item xsi:type="xsd:string">toBeDeletedDate</item>
                   <item xsi:type="xsd:string">status</item>
                   <item xsi:type="xsd:string">regStatus</item>
                   <item xsi:type="xsd:string">trusteeWPP</item>
                </fields>
                <clientTRID xsi:type="xsd:string"></clientTRID>
                <forReseller xsi:type="xsd:string"></forReseller>
             </domainListExtendedRequest>
          </ns:domainListExtended>
       </soapenv:Body>
    </soapenv:Envelope>
    """

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
            url, data=soap_body, headers=headers,
            auth=HTTPBasicAuth(username, password)
        )
        status_code = response.status_code

        if response.status_code != 200:
            error_msg = f"Unexpected response. Status code: {response.status_code}, Response Text: {response.text}"
            logging.error(error_msg)
        else:
            root = ET.fromstring(response.text)

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
                            f'domain="{domain_data.get("domainName", "")}", '
                            f'reg_type="{domain_data.get("regType", "")}", '
                            f'reseller="{domain_data.get("reseller", "")}", '
                            f'adminC="{domain_data.get("adminC", "")}", '
                            f'ownerC="{domain_data.get("ownerC", "")}", '
                            f'techC="{domain_data.get("techC", "")}", '
                            f'zoneC="{domain_data.get("zoneC", "")}", '
                            f'nameserver="{domain_data.get("nameserver", "")}", '
                            f'status="{domain_data.get("status", "")}", '
                            f'domainStatus="{domain_data.get("domainStatus", "")}", '
                            f'regStatus="{domain_data.get("regStatus", "")}", '
                            f'systemInDate="{domain_data.get("systemInDate", "")}", '
                            f'orderDate="{domain_data.get("orderDate", "")}", '
                            f'orderNumber="{domain_data.get("orderNumber", "")}", '
                            f'toBeDeletedDate="{domain_data.get("toBeDeletedDate", "")}", '
                            f'trusteeWPP="{domain_data.get("trusteeWPP", "")}", '
                            f'irtpStatus="{domain_data.get("irtpStatus", "")}"'
                            f'}} 1'
                        )
                        metrics.append(metric_line)

            status = "success"

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Exception during fetch: {error_msg}")

    timestamp = int(time.time())

    metrics.append("# HELP domain_fetch_success Was the last fetch successful (1) or not (0)")
    metrics.append("# TYPE domain_fetch_success gauge")
    metrics.append(
        f'domain_fetch_success{{timestamp="{timestamp}", status="{status}", code="{status_code}", error="{error_msg}"}} {1 if status == "success" else 0}'
    )

    metrics.append("# HELP domain_fetch_timestamp Unix timestamp of last fetch attempt")
    metrics.append("# TYPE domain_fetch_timestamp gauge")
    metrics.append(
        f'domain_fetch_timestamp{{status="{status}", code="{status_code}", error="{error_msg}"}} {timestamp}'
    )

    with open(output_file, "w") as f:
        f.write("# HELP domain_info Domain state with extra labels\n")
        f.write("# TYPE domain_info gauge\n")
        for line in metrics:
            f.write(f"{line}\n")

    logging.info(f"Wrote {len(metrics)} metrics to {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, help="Interval in Seconds (Default: EXPORT_INTERVAL)")
    parser.add_argument("--output", help="Path for metrics (Default: EXPORT_OUTPUT)")
    parser.add_argument("--username", help="Username (Default: EXPORT_USER)")
    parser.add_argument("--password", help="Password (Default: EXPORT_PASS)")
    args = parser.parse_args()

    interval, interval_source = get_config_value(args.interval, "EXPORT_INTERVAL", default=300, cast=int)
    output, output_source = get_config_value(args.output, "EXPORT_OUTPUT", default="metrics/ext_domain_metrics.prom")
    username, user_source = get_config_value(args.username, "EXPORT_USER", required=True)
    password, pass_source = get_config_value(args.password, "EXPORT_PASS", required=True)

    logging.info("Configuration used:")
    logging.info(f"  Interval: {interval} (source: {interval_source})")
    logging.info(f"  Output: {output} (source: {output_source})")
    logging.info(f"  Username: {username} (source: {user_source})")
    logging.info(f"  Password: {'*' * len(password)} (source: {pass_source})")

    while True:
        fetch_and_write_metrics(output, username, password)
        time.sleep(interval)

if __name__ == "__main__":
    main()
