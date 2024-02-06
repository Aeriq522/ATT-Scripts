import requests
import json
import csv
from pprint import pprint
from google.cloud import secretmanager

# Function to fetch GCP credentials from Secret Manager
def access_secret_version():
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": f"projects/probable-anchor-272920/secrets/att-machine-credentials/versions/latest"})
    id, s = json.loads(response.payload.data.decode('UTF-8')).values()
    return id, s

# Default headers
def get_default_headers(id, s):
    return {
        'app-id': id,
        'app-secret': s,
        'Cache-Control': "no-cache",
        'Host': "https://apsapi.att.com:8082"
    }


# Function to get line info for a subscriber number
def get_line_info(subscriber_number: str, headers):
    url = "https://apsapi.att.com:8082/sp/mobility/lineconfig/api/v1/service/" + subscriber_number
    
    try:
        response = requests.get(url=url, headers=headers)
        result_string = "Status Code: " + str(response.status_code) + " MDN: " + subscriber_number
        print(result_string)
        
        # Load JSON data
        data_dict = response.json()
        pprint(data_dict.get("status"))
        
        return {'status_code': response.status_code, 'mdn': subscriber_number}
    except Exception:
        return {'status_code': 900, 'mdn': subscriber_number}
        
    
# get_line_info('7606811465')

# Read subscriber numbers from CSV file
csv_file = "C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/subscriber_numbers.csv"
with open(csv_file, newline='') as csvfile:
    reader = csv.reader(csvfile)
    # next(reader)  # Skip header if exists
    id, s = access_secret_version()
    headers = get_default_headers(id, s)
    
    for row in reader:
        subscriber_number = row[0]  # Assuming subscriber number is in the first column
        get_line_info(subscriber_number, headers)


print('Done')

