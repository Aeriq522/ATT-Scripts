import requests
import json
import csv
from pprint import pprint
import threading
import time
from att_serviceCharacteristics import service_characteritics_names
from google.cloud import secretmanager

THREADS = 12

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


# Function to get line info for a subscriber number
def get_line_info(subscriber_number: str, headers, characteristic_names):
    url = (
        "https://apsapi.att.com:8082/sp/mobility/lineconfig/api/v1/service/"
        + subscriber_number
    )

    try:
        response = requests.get(url=url, headers=headers)
        result_string = (
            "Status Code: " + str(response.status_code) + " MDN: " + subscriber_number
        )
        print(result_string)
        # pprint(response.content)

        # Load JSON data
        data_dict = response.json()

        # Extract the value of "serviceZipCode" from the nested structure, can extract any other value same way
        service_characteristic = data_dict.get("serviceCharacteristic", [])
        found_characteristics = {}

        for characteristic in service_characteristic:
            name = characteristic.get("name")
            value = characteristic.get("value")

            if name in characteristic_names:
                found_characteristics[name] = value
                print(f"{name}: {value}")  # print success message with found results

        for name in characteristic_names:
            if name not in found_characteristics:
                print(f"{name} not found")  # print failed message with found results

        return [
            found_characteristics.get(name, "") for name in characteristic_names
        ]  # Return a list of values for each characteristic name

    except Exception as e:
        # Exception handling
        print("Exception occurred:", e)
        return {"status_code": 900, "mdn": subscriber_number}


# Function to process subscriber numbers
def process_subscriber_numbers(reader, writer, headers, characteristic_names):
    for row in reader:
        subscriber_number = row[0]
        values = get_line_info(subscriber_number, headers, characteristic_names)
        if (
            values is not None
        ):  # Check if values is None before attempting to concatenate
            values_to_write = [
                subscriber_number
            ] + values  # Row with found values and adding the Subscriber number to be written in csv
        else:
            values_to_write = [subscriber_number] + [""] * len(
                characteristic_names
            )  # Fill with empty strings if no values found
        writer.writerow(
            values_to_write
        )  # subscriberNumber,subscriberStatus,serviceZipCode will be printed for now


def run_threads(reader, writer, headers, characteristic_names):
    threads = []
    for _ in range(THREADS):  # Number of threads
        thread = threading.Thread(
            target=process_subscriber_numbers,
            args=(reader, writer, headers, characteristic_names),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


# Read subscriber numbers from CSV file, Output CSV file
csv_file = "C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/CheckForIntBlock/GetRequestForBlockCode/subscriber_numbers.csv"
output_file = "C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/CheckForIntBlock/GetRequestForBlockCode/line_info_results.csv"

start_time = time.time()

with open(csv_file, newline="") as csvfile, open(
    output_file, "w", newline=""
) as csvfile_output:
    reader = csv.reader(csvfile)
    writer = csv.writer(csvfile_output)
    characteristic_names = [
        service_characteritics_names[0],  # subscriberStatus - Current status of the subscriber
        service_characteritics_names[1],  # statusEffectiveDate - The effective date of the current status
        service_characteritics_names[2],  # statusReasonCode - Code explaining the reason for the current status
        # service_characteritics_names[3],  # subscriberActivationDate - Date the subscriber was activated
        service_characteritics_names[4],  # singleUserCode - Unique code for a user
        service_characteritics_names[5],  # singleUserCodeDescription - Description of the single user code
        # service_characteritics_names[6],  # serviceZipCode - Zip code where the service is registered
        # service_characteritics_names[7],  # effectiveDate - Start date of the service effectiveness
        # service_characteritics_names[8],  # expirationDate - End date of the service effectiveness
        # service_characteritics_names[9],  # billingAccountNumber - Account number used for billing
        # service_characteritics_names[10], # nextBillCycleDate - Date of the next billing cycle
        service_characteritics_names[11], # contactName - Contact name associated with the account
        service_characteritics_names[12], # sim - SIM card identifier
        # service_characteritics_names[13], # pendingEquipmentUpgrade - Indicator of a pending equipment upgrade
        # service_characteritics_names[14], # BLIMEI - Baseband Layer IMEI
        # service_characteritics_names[15], # BLIMEIType - Type of the Baseband Layer IMEI
        # service_characteritics_names[16], # BLDeviceBrand - Brand of the Baseband Layer device
        # service_characteritics_names[17], # BLDeviceModel - Model of the Baseband Layer device
        # service_characteritics_names[18], # BLDeviceTechnologyType - Technology type of the Baseband Layer device
        service_characteritics_names[19],  # NWIMEI - Network IMEI, a unique identifier for mobile devices
        # service_characteritics_names[20],  # NWIMEIType - Type or category of the Network IMEI
        # service_characteritics_names[21],  # NWDeviceBrand - Brand of the network device
        # service_characteritics_names[22],  # NWDeviceModel - Model of the network device
        # service_characteritics_names[23],  # osVersion - Operating system version of the device
        # service_characteritics_names[24],  # osType - Type of operating system (Android, iOS, etc.)
        # service_characteritics_names[25],  # imeiVersion - Version of the International Mobile Equipment Identity
        service_characteritics_names[26],  # offeringCode1 - Code for the first service or product offering
        service_characteritics_names[27],  # offeringDescription1 - Description of the first offering
        # service_characteritics_names[28],  # offeringEffectiveDate1 - Effective date of the first offering
        # service_characteritics_names[29],  # offeringExpirationDate1 - Expiration date of the first offering
        service_characteritics_names[30],  # offeringCode2 - Code for the second service or product offering
        service_characteritics_names[31],  # offeringDescription2 - Description of the second offering
        # service_characteritics_names[32],  # offeringEffectiveDate2 - Effective date of the second offering
        # service_characteritics_names[33],  # offeringExpirationDate2 - Expiration date of the second offering
        service_characteritics_names[34],  # offeringCode3 - Code for the second service or product offering
        service_characteritics_names[35],  # offeringDescription3 - Description of the third offering
        # service_characteritics_names[36],  # offeringEffectiveDate3 - Effective date
        # service_characteritics_names[37],  # offeringExpirationDate3 - Expiration date of the third
        service_characteritics_names[38],  # offeringCode4 - Code for the fourth service or product
        service_characteritics_names[39],  # offeringDescription4 - Description of the fourth service or product
    ]

    header_row = ["subscriberNumber"] + characteristic_names
    writer.writerow(header_row)

    # next(reader)  # Skip header if exists
    id, s = access_secret_version()
    headers = get_default_headers(id, s)

    run_threads(reader, writer, headers, characteristic_names)

end_time = time.time()
print("Done")
print(f"Execution time: {end_time - start_time} seconds")

