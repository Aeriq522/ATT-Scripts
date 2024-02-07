import requests
import json
import csv

from google.cloud import secretmanager
from requests import RequestException

import update_IMEIs

success_value = "success"
failure_value = "failure"


# Function to fetch GCP credentials from Secret Manager
def access_secret_version():
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(
        request={
            "name": f"projects/probable-anchor-272920/secrets/att-machine-credentials/versions/latest"
        }
    )
    id, s = json.loads(response.payload.data.decode("UTF-8")).values()
    return id, s


# Default headers
def get_default_headers(id, s):
    return {
        "app-id": id,
        "app-secret": s,
        "Cache-Control": "no-cache",
        "Host": "https://apsapi.att.com:8082",
    }


def change_data_plan(subscriber_number: str, headers, singleUserCode, effectiveDate):
    url = (
        "https://apsapi.att.com:8082/sp/mobility/lineconfig/api/v1/service/"
        + subscriber_number
    )

    data = {
        "effectiveDate": effectiveDate,
        "serviceCharacteristic": [
            # {"name": "reasonCode", "value": reasonCode},
            {"name": "singleUserCode", "value": singleUserCode},
            # {"name": "technologyType", "value": technologyType},
            # {"name": "IMEI", "value": IMEI}
        ],
    }

    try:
        response = requests.patch(url=url, headers=headers, json=data)

        print(f"Status Code: {str(response.status_code)} MDN: {subscriber_number}")

        if response.status_code == 200:
            return {
                "mdn": {subscriber_number},
                "result": success_value,
                "result_code": 200,
                "result_message": "Service plan changed successfully.",
            }
        else:
            return {
                "mdn": {subscriber_number},
                "result": failure_value,
                "result_code": response.status_code,
                "result_message": "Service plan changed successfully.",
            }

    except RequestException:
        connection_error_code = 920
        connection_error_message = "Connection failed successfully."
        print(f"Status Code: {connection_error_code} MDN: {subscriber_number}")
        return {
            "mdn": {subscriber_number},
            "result": failure_value,
            "result_code": connection_error_code,
            "result_message": connection_error_message,
        }

# Read subscriber numbers from CSV file
csv_file = "C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/planChange.csv"
with open(csv_file, newline="") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header if exists
    id, s = access_secret_version()
    headers = get_default_headers(id, s)

    # Iterate over each row in the CSV
    for row in reader:
        (
            subscriber_number,
            singleUserCode,
            effectiveDate,
            IMEI,
            reasonCode,
            serviceZipCode,
            technologyType,
        ) = row
        update_IMEIs.update_IMEIs(
            subscriber_number,
            headers,
            singleUserCode,
            IMEI,
            reasonCode,
            serviceZipCode,
            technologyType,
        )
        change_data_plan(subscriber_number, headers, singleUserCode, effectiveDate)
print("Done")
