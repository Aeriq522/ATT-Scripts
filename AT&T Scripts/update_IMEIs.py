import requests
import json
from google.cloud import secretmanager



client = secretmanager.SecretManagerServiceClient()
response = client.access_secret_version(request={"name": f"projects/probable-anchor-272920/secrets/att-machine-credentials/versions/latest"})
id, s = json.loads(response.payload.data.decode('UTF-8')).values()

default_headers = {
    'app-id': id,
    'app-secret': s,
    'Cache-Control': "no-cache",
    'Host': "https://apsapitest01.att.com:8082"
}

def get_line_info(subscriber_number: str):
    # subscriber_number = '7608058882'
    url = "https://https://apsapitest01.att.com:8082/sp/mobility/service/" + subscriber_number
    data = {
        "mode": "R",
        # "reasonCode": "CR"
    }
    try:
        response = requests.get(url=url, headers=default_headers, json=data)
        result_string = "Status Code: " + str(response.status_code) + " MDN: " + subscriber_number
        print(result_string)
        return {'status_code': response.status_code, 'mdn': subscriber_number}
    except Exception:
        return {'status_code': 900, 'mdn': subscriber_number}
    
get_line_info('7608058882')

print('Done')

