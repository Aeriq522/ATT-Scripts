import json
import time
import csv
import requests
from google.cloud import secretmanager
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime
import progressbar



# Set the maximum number of threads
max_threads = 10  # You can adjust this number based on your system capabilities
    
current_time = datetime.now().strftime("%m-%d-%Y_%H.%M")  # Format: Month-Day-Year_Hour:Minute

mdns_to_check = "C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/CheckForIntBlock/GETIntBlockCode/mdns_to_check.csv"

active_mdns_file = f"C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/CheckForIntBlock/Logging/Active/active_subscribers_{current_time}.csv"
suspended_mdns_file = f"C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/CheckForIntBlock/Logging/Suspended/suspended_subscribers_{current_time}.csv"

def read_mdn_list(filename):
    with open(filename, mode="r", newline="") as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip the header row if there is one
        return [row[0] for row in reader]
    

# Connect to ATT Servers and GET line information for MDNs input
class ATTServiceManager:
    def __init__(self):
        self.client = secretmanager.SecretManagerServiceClient()
        self.credentials = self.load_credentials()

    def load_credentials(self):
        # Fetch credentials securely from GCP Secret Manager
        response = self.client.access_secret_version(
            request={
                "name": "projects/probable-anchor-272920/secrets/att-machine-credentials/versions/latest"
            }
        )
        # Decode the JSON payload into a dictionary
        credentials = json.loads(response.payload.data.decode("UTF-8"))
        return credentials

    def get_default_headers(self):
        # print(self.credentials)
        # Use credentials to set headers for API requests
        return {
            "app-id": self.credentials["app-id"],
            "app-secret": self.credentials["app-secret"],
            "Cache-Control": "no-cache",
            "Host": "https://apsapi.att.com:8082",
        }

    def get_line_info(self, subscriber_number):
        headers = self.get_default_headers()
        url = (
            "https://apsapi.att.com:8082/sp/mobility/lineconfig/api/v1/service/"
            + str(subscriber_number)
        )
        attempts = 3  # Number of attempts
        for attempt in range(attempts):
            try:
                response = requests.get(url=url, headers=headers, timeout=10)  # Adding a timeout of 10 seconds
                result_string = (
                    f"Status Code: {response.status_code} MDN: {subscriber_number}"
                )
                # print(result_string)
                # print(response.json())
                if response.status_code != 200:
                    # Log any non-200 responses to CSV
                    error_desc = self.extract_error_description(response)
                    self.log_error_to_csv(
                        response.status_code, error_desc, subscriber_number
                    )
                    return {
                        "status_code": response.status_code,
                        "mdn": subscriber_number,
                        "error": error_desc,
                    }
                return response.json()
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < attempts - 1:
                    time.sleep(5)  # Wait for 5 seconds before retrying
                else:
                    # Final attempt: Log the error to CSV
                    self.log_error_to_csv(subscriber_number, 900, str(e))
                    return {"status_code": 900, "mdn": subscriber_number, "error": str(e)}

    def extract_error_description(self, response):
        try:
            # Safely attempt to extract the error description from the response
            return response.json().get(
                "errorDescription", "No error description provided"
            )
        except ValueError:
            # Handle cases where the response is not in JSON format
            return "Invalid JSON response"

    def log_error_to_csv(self, subscriber_number, status_code, error_description):
        with open(
            "C:/Users/eriks/AppData/Local/Programs/Python/Python312/Scripts/AT&T Scripts/CheckForIntBlock/Logging/MDNErrors/MDN_errors.csv",
            "a",
            newline="",
        ) as file:
            writer = csv.writer(file)
            writer.writerow([subscriber_number, status_code, error_description])


# Verify if MDN is active, and shouldUpdate
class ServiceDataValidator:
    def __init__(self, single_user_codes, total_count):
        self.manager = ATTServiceManager()
        self.single_user_codes = single_user_codes
        self.lock = threading.Lock()  # For file writing
        self.count_lock = threading.Lock()  # For safely incrementing the count
        self.processed_count = 0
        self.progress_bar = progressbar.ProgressBar(max_value=total_count, redirect_stdout=True)

    def process_number(self, subscriber_number, total_count):
        line_info = self.manager.get_line_info(subscriber_number)
        if line_info:
            service_characteristics = line_info.get("serviceCharacteristic", [])
            subscriber_status = self.get_subscriber_status(service_characteristics)
            if self.is_valid_single_user_code(service_characteristics):
                offering_codes = self.extract_offering_codes(
                    subscriber_number, service_characteristics
                )
                if "NIRM" not in offering_codes:
                    self.write_to_csv(subscriber_number, subscriber_status, offering_codes)
        # Update progress after processing each MDN
        with self.count_lock:
            self.processed_count += 1
            self.progress_bar.update(self.processed_count)

    def is_valid_single_user_code(self, characteristics):
        for item in characteristics:
            if (
                item["name"] == "singleUserCode"
                and item["value"] in self.single_user_codes
            ):
                return True
        return False

    def cleanup_invalid_user_code(self, subscriber_number):
        # Remove data if single user code is invalid
        if subscriber_number in self.valid_data:
            del self.valid_data[subscriber_number]

    def extract_offering_codes(self, subscriber_number, characteristics):
        return {
            item["value"] for item in characteristics if "offeringCode" in item["name"]
        }

    def cleanup_memory(self):
        # Remove all entries that do not meet the condition (missing 'NIRM')
        self.valid_data = {k: v for k, v in self.valid_data.items() if "NIRM" not in v}

    def get_subscriber_status(self, characteristics):
        for item in characteristics:
            if item["name"] == "subscriberStatus":
                return item["value"]
        return None

    def write_to_csv(self, mdn, status, offering_codes):
        filename = active_mdns_file if status == "A" else suspended_mdns_file
        with self.lock:
            with open(filename, "a", newline="") as file:
                writer = csv.writer(file)
                row_data = [mdn, status] + list(offering_codes)
                writer.writerow(row_data)


def main():
    single_user_codes = ["APX1G5M30", "APX1GBT30", "APX1GBM30", "APX1GBP30"]
    mdn_list = read_mdn_list(mdns_to_check)
    total_count = len(mdn_list)
    
    validator = ServiceDataValidator(single_user_codes, total_count)

    # Prepare CSV files with headers
    headers = ["MDN", "Status"] + [f"Offering Code {i+1}" for i in range(10)]  # Adjust based on expected max offering codes
    for filename in [active_mdns_file, suspended_mdns_file]:
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for mdn in mdn_list:
            executor.submit(validator.process_number, mdn, total_count)

    validator.progress_bar.finish()

    end_time = time.time()
    elapsed_time = end_time - start_time
    
    if elapsed_time < 60:
        print(f"Elapsed Time: {elapsed_time:.2f} seconds")
    else:
        minutes = int(elapsed_time // 60)
        remainder_seconds = elapsed_time % 60
        print(f"Elapsed Time: {minutes} minutes and {remainder_seconds:.2f} seconds")

if __name__ == "__main__":
    main()
