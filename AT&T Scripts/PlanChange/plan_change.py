import requests
import json
import csv
import concurrent.futures
from google.cloud import secretmanager

# Function to fetch GCP credentials from Secret Manager
def access_secret_version():
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(
        request={"name": "projects/probable-anchor-272920/secrets/att-machine-credentials/versions/latest"}
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

# Function to update plans
def update_plans(subscriber_data):
    subscriber_number, headers, effectiveDate, singleUserCode = subscriber_data
    url = "https://apsapi.att.com:8082/sp/mobility/lineconfig/api/v1/service/" + subscriber_number
    
    data = {
        "effectiveDate": effectiveDate,
        "serviceCharacteristic": [
            {"name": "singleUserCode", "value": singleUserCode},
        ]
    }
    
    try:
        response = requests.patch(url=url, headers=headers, json=data)
        result_string = "Status Code: " + str(response.status_code) + " MDN: " + subscriber_number
        print(result_string)
        print(response.content)
        
        return {'status_code': response.status_code, 'mdn': subscriber_number}
    except Exception:
        return {'status_code': 900, 'mdn': subscriber_number}

# Read subscriber numbers from CSV file
csv_file = "C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/planChange.csv"
output_file = "C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/planchange_result.csv"

with open(csv_file, newline="") as csvfile, open(output_file, 'w', newline='') as csvfile_output:
    reader = csv.reader(csvfile)
    writer = csv.writer(csvfile_output)
    writer.writerow(['Status Code', 'MDN'])
    
    next(reader)  # Skip header if exists
    id, s = access_secret_version()
    headers = get_default_headers(id, s)

    # Create a thread pool with 4 workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Iterate over each row in the CSV
        for row in reader:
            (
                subscriber_number,
                singleUserCode,
                effectiveDate,
                IMEI,
            ) = row
            subscriber_data = (
                subscriber_number,
                headers,
                effectiveDate,
                singleUserCode,
            )
            # Submit the update_plans function to the executor
            future = executor.submit(update_plans, subscriber_data)
            result = future.result()
            status = "Success" if 200 <= result['status_code'] < 300 else ("Failure" if result['status_code'] >= 400 else "Review")
            writer.writerow([status, result['status_code'], result['mdn']])
    
print("Done")
