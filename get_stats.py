import requests
import json
import time
import concurrent.futures
from datetime import datetime, timedelta
import signal
import sys
import os
import argparse

# Configurable variables
psu_output_file = "psu_readings.json"
fan_output_file = "fan_readings.json"
temp_output_file = "temp_readings.json"

# Define the argument parser
parser = argparse.ArgumentParser(description='Collect stats from the server.')
parser.add_argument('--bmc-ip', required=True, help='Server BMC IP address')
parser.add_argument('--bmc-username', required=True, help='Username for authentication')
parser.add_argument('--probe-every', required=True, type=int, help='Probe interval in seconds')
parser.add_argument('--collect-for', type=int, help='Duration in seconds for which to collect data. Runs indefinitely if not specified.')
args = parser.parse_args()

# Extract arguments
server_ip = args.bmc_ip
username = args.bmc_username
probe_every = args.probe_every
collect_duration = args.collect_for

# Get the password from environment variable
password = os.getenv('BMC_PASSWORD')
if not password:
    print("Error: BMC_PASSWORD environment variable not set.")
    print("Example: export BMC_PASSWORD='your_password'")
    sys.exit(1)

# Minimum allowed probe interval
MIN_PROBE_INTERVAL = 15

# Base URLs for Redfish API
psu_base_url = f"https://{server_ip}/redfish/v1/Chassis/Miramar_Sensor/Sensors"
fan_base_url = f"https://{server_ip}/redfish/v1/Chassis/Miramar_Sensor/Thermal"
temp_base_url = f"https://{server_ip}/redfish/v1/Chassis/Miramar_Sensor/Thermal"

# Disable warnings about self-signed certificates
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def get_psu_endpoints():
    """Query the system to get PSU endpoints."""
    response = requests.get(psu_base_url, auth=(username, password), verify=False)
    response.raise_for_status()
    data = response.json()
    
    gpu_psu_endpoints = [member["@odata.id"] for member in data["Members"] if "power_PWR_PDB_" in member["@odata.id"]]
    cpu_psu_endpoints = [member["@odata.id"] for member in data["Members"] if "PWR_MB_PSU" in member["@odata.id"]]
    
    return gpu_psu_endpoints, cpu_psu_endpoints

def parse_psu_name(member_id, is_gpu=True):
    """Parse the PSU name based on the member ID convention."""
    if is_gpu:
        return member_id.replace("power_PWR_PDB_PSU", "GPU_TRAY_PSU")
    else:
        return member_id.replace("PWR_MB_PSU", "CPU_TRAY_PSU")

def query_psu(psu_url, is_gpu=True):
    """Query each PSU and return the name, timestamp, and reading value."""
    response = requests.get(f"https://{server_ip}{psu_url}", auth=(username, password), verify=False)
    response.raise_for_status()
    data = response.json()
    reading = data.get("Reading", "N/A")
    timestamp = datetime.utcnow().isoformat()
    member_id = psu_url.split("/")[-1]
    name = parse_psu_name(member_id, is_gpu)
    return {
        "Name": name,
        "Timestamp": timestamp,
        "Reading": reading
    }

def get_fan_data():
    """Query the system to get fan data."""
    response = requests.get(fan_base_url, auth=(username, password), verify=False)
    response.raise_for_status()
    data = response.json()
    return data.get("Fans", [])

def parse_fan_name(member_id):
    """Parse the fan name based on the member ID convention."""
    member_id = member_id.replace("SPD_", "")
    if member_id.endswith("_F"):
        return member_id.replace("_F", " Front")
    elif member_id.endswith("_R"):
        return member_id.replace("_R", " Rear")
    return member_id

def query_fan(fan_data):
    """Query each fan and return the name, timestamp, and reading value."""
    reading = fan_data.get("Reading", "N/A")
    timestamp = datetime.utcnow().isoformat()
    member_id = fan_data.get("MemberId", "Unknown")
    name = parse_fan_name(member_id)
    return {
        "Name": name,
        "Timestamp": timestamp,
        "Reading": reading
    }

def get_temp_data():
    """Query the system to get temperature data."""
    response = requests.get(temp_base_url, auth=(username, password), verify=False)
    response.raise_for_status()
    data = response.json()
    return data.get("Temperatures", [])

def parse_temp_name(member_id):
    """Parse the temperature name based on the member ID convention."""
    if "TEMP_PDB_PSU" in member_id:
        return member_id.replace("TEMP_PDB_PSU", "TEMP_GPU_TRAY_PSU")
    elif "TEMP_MB_PSU" in member_id:
        return member_id.replace("TEMP_MB_PSU", "TEMP_CPU_TRAY_PSU")
    else:
        return member_id

def query_temp(temp_data):
    """Query each temperature sensor and return the name, timestamp, and reading value."""
    reading = temp_data.get("ReadingCelsius", "N/A")
    timestamp = datetime.utcnow().isoformat()
    member_id = temp_data.get("MemberId", "Unknown")
    name = parse_temp_name(member_id)
    return {
        "Name": name,
        "Timestamp": timestamp,
        "Reading": reading
    }

def append_to_json_file(file_path, data):
    """Append new data to the JSON file."""
    try:
        with open(file_path, "r") as f:
            if f.read().strip():  # Check if file is not empty
                f.seek(0)  # Go back to the beginning of the file
                existing_data = json.load(f)
            else:
                existing_data = []
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    existing_data.extend(data)  # Append the new data to the existing data

    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=4)

def signal_handler(sig, frame):
    """Handle the interrupt signal to gracefully exit."""
    print("\nInterrupt received, shutting down...")
    sys.exit(0)

def main():
    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)
    
    # Enforce minimum probe interval
    if probe_every < MIN_PROBE_INTERVAL:
        print(f"Error: probe_every cannot be lower than {MIN_PROBE_INTERVAL} seconds.")
        sys.exit(1)
    
    # Get PSU endpoints
    gpu_psu_endpoints, cpu_psu_endpoints = get_psu_endpoints()
    
    # Calculate the end time for data collection if --collect-for is specified
    end_time = datetime.utcnow() + timedelta(seconds=collect_duration) if collect_duration else None
    
    while True:
        if end_time and datetime.utcnow() >= end_time:
            print("Data collection completed.")
            break

        psu_readings = []
        total_power = 0.0
        
        # Query each GPU PSU in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_psu = {executor.submit(query_psu, psu, True): psu for psu in gpu_psu_endpoints}
            for future in concurrent.futures.as_completed(future_to_psu):
                psu = future_to_psu[future]
                try:
                    data = future.result()
                    psu_readings.append(data)
                    if data["Reading"] != "N/A":
                        total_power += float(data["Reading"])
                except Exception as exc:
                    print(f"Exception occurred while querying {psu}: {exc}")
        
        # Query each CPU Tray PSU in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_psu = {executor.submit(query_psu, psu, False): psu for psu in cpu_psu_endpoints}
            for future in concurrent.futures.as_completed(future_to_psu):
                psu = future_to_psu[future]
                try:
                    data = future.result()
                    # Correct the name format
                    data["Name"] = data["Name"].replace("power_", "")
                    psu_readings.append(data)
                    if data["Reading"] != "N/A":
                        total_power += float(data["Reading"])
                except Exception as exc:
                    print(f"Exception occurred while querying {psu}: {exc}")
        
        # Add total power consumption to the readings
        timestamp = datetime.utcnow().isoformat()
        psu_readings.append({
            "Name": "Total Power in W",
            "Timestamp": timestamp,
            "Reading": total_power
        })
        
        # Append PSU readings to JSON file
        append_to_json_file(psu_output_file, psu_readings)
        
        # Get Fan data in parallel
        fan_readings = []
        fan_data_list = get_fan_data()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_fan = {executor.submit(query_fan, fan_data): fan_data for fan_data in fan_data_list}
            for future in concurrent.futures.as_completed(future_to_fan):
                fan_data = future_to_fan[future]
                try:
                    data = future.result()
                    fan_readings.append(data)
                except Exception as exc:
                    print(f"Exception occurred while querying {fan_data}: {exc}")
        
        # Append Fan readings to JSON file
        append_to_json_file(fan_output_file, fan_readings)
        
        # Get Temperature data in parallel
        temp_readings = []
        temp_data_list = get_temp_data()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_temp = {executor.submit(query_temp, temp_data): temp_data for temp_data in temp_data_list}
            for future in concurrent.futures.as_completed(future_to_temp):
                temp_data = future_to_temp[future]
                try:
                    data = future.result()
                    temp_readings.append(data)
                except Exception as exc:
                    print(f"Exception occurred while querying {temp_data}: {exc}")
        
        # Append Temperature readings to JSON file
        append_to_json_file(temp_output_file, temp_readings)
        
        # Wait for the next probe cycle
        time.sleep(probe_every)

if __name__ == "__main__":
    main()