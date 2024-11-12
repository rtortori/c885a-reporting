# Cisco UCS C885A - Monitoring and Reporting

Disclaimer: This is NOT an official Cisco application and comes with absolute NO WARRANTY!<br>
Please check the [LICENSE](https://github.com/rtortori/c885a-reporting/blob/main/LICENSE-CISCO.md ) for further information. <br>

## Abstract

This project provides a set of scripts to collect, analyze, and generate reports on the performance metrics of the Cisco UCS C885A system. The data includes power usage, fan speeds, and temperatures from various components. The collected data is processed to generate plots and a comprehensive PDF report. Data is collecting using Redfish APIs

## Directory Structure

When collecting stats and plotting data, the following files and directories are created:

- **psu_readings.json**: Stores the power supply unit (PSU) readings.
- **fan_readings.json**: Stores the fan speed readings.
- **temp_readings.json**: Stores the temperature readings.
- **Reports/**: A directory created for each report generation run, labeled with the timestamp.
  - **psus/**: Contains plots related to PSU usage.
  - **fans/**: Contains plots related to fan speeds.
  - **temperatures/**: Contains plots related to component temperatures.
  - **report.pdf**: The final PDF report combining all plots and analyses, labeled with the timestamp.

## Installation

To set up and run the scripts, follow these steps:

1. **Clone the repository**:

```bash
git clone https://github.com/rtortori/c885a-reporting.git
cd c885a-reporting
```

2. **Install Python dependencies**:

```bash
pip install -r requirements.txt
```

3. **Install CairoSVG**:
Depending on your operating system, you may need to install CairoSVG separately. Instructions vary, but typically you can use a package manager like apt for Ubuntu or brew for macOS:

```bash
# On Ubuntu
sudo apt-get install libcairo2-dev libjpeg-dev libgif-dev

# On macOS
brew install cairo
```

## Usage

### Collecting Stats

Set your BMC password as an environment variable:

```bash
export BMC_PASSWORD='your_password'
```

Use `get_stats.py` to collect performance metrics from the server. By default it will run indefinitely (stop with `kill` or `CTRL+C`):

```bash
% python get_stats.py -h                                                                          
usage: get_stats.py [-h] --bmc-ip BMC_IP --bmc-username BMC_USERNAME --probe-every PROBE_EVERY [--collect-for COLLECT_FOR]

Collect stats from the server.

options:
  -h, --help            show this help message and exit
  --bmc-ip BMC_IP       Server BMC IP address
  --bmc-username BMC_USERNAME
                        Username for authentication
  --probe-every PROBE_EVERY
                        Probe interval in seconds
  --collect-for COLLECT_FOR
                        Duration in seconds for which to collect data. Runs indefinitely if not specified.
```

```bash
python get_stats.py --server-ip=X.Y.Z.K --username=mybmcusername --probe-every=15
```

### Generating Plots and Reports

Use `plot_stats.py` to generate plots and a PDF report from the collected data:

```bash
% python plot_stats.py -h
usage: plot_stats.py [-h] [--resample RESAMPLE]

Generate plots and reports from sensor data.

options:
  -h, --help           show this help message and exit
  --resample RESAMPLE  Number of samples to skip for each sensor. Default is 1 (consider all samples).
```

```bash
python plot_stats.py --resample 2 #Use higher numbers to reduce plot density.
```

## Examples

### Fan Readings (fan_readings.json)

```
[...]
    {
        "Name": "FAN15 Rear",
        "Timestamp": "2024-11-11T17:49:29.831021",
        "Reading": 11843.0
    },
    {
        "Name": "FAN12 Front",
        "Timestamp": "2024-11-11T17:49:29.830706",
        "Reading": 7801.0
    },
    {
        "Name": "FAN2 Rear",
        "Timestamp": "2024-11-11T17:49:29.831356",
        "Reading": 3343.0
    },
    {
        "Name": "FAN13 Front",
        "Timestamp": "2024-11-11T17:49:29.830853",
        "Reading": 10802.0
    },
    {
        "Name": "FAN6 Rear",
        "Timestamp": "2024-11-11T17:49:29.831839",
        "Reading": 3355.0
    },
[...]
```

### PSU Readings (psu_readings.json)

```
[...]
    {
        "Name": "GPU_TRAY_PSU5",
        "Timestamp": "2024-11-11T17:49:25.587369",
        "Reading": 213.0
    },
    {
        "Name": "GPU_TRAY_PSU4",
        "Timestamp": "2024-11-11T17:49:25.596474",
        "Reading": 140.0
    },
    {
        "Name": "GPU_TRAY_PSU1",
        "Timestamp": "2024-11-11T17:49:25.599200",
        "Reading": 154.0
    },
    {
        "Name": "GPU_TRAY_PSU6",
        "Timestamp": "2024-11-11T17:49:25.604925",
        "Reading": 140.0
    },
    {
        "Name": "GPU_TRAY_PSU3",
        "Timestamp": "2024-11-11T17:49:25.607462",
        "Reading": 254.0
    },
[...]
```

### Temperatures Readings (temp_readings.json)

```
[...]
    {
        "Name": "TEMP_NVME_10",
        "Timestamp": "2024-11-11T17:50:31.230620",
        "Reading": 39.0
    },
    {
        "Name": "TEMP_GB_GPU3_M",
        "Timestamp": "2024-11-11T17:50:31.229829",
        "Reading": 43.0
    },
    {
        "Name": "TEMP_GB_HSC1",
        "Timestamp": "2024-11-11T17:50:31.229916",
        "Reading": 33.0
    },
    {
        "Name": "TEMP_AMBIENT",
        "Timestamp": "2024-11-11T17:50:31.229364",
        "Reading": 24.0
    },
    {
        "Name": "TEMP_GB_GPU5",
        "Timestamp": "2024-11-11T17:50:31.229840",
        "Reading": 33.0
    },
[...]
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.