import os
import argparse
from datetime import datetime
from utils import load_data, plot_psu_power_usage, plot_psu_breakdown, plot_fan_speed, plot_fan_aggregate, plot_temperature_data, create_pdf_report
import finalize_report

# File paths
psu_file = "psu_readings.json"
fan_file = "fan_readings.json"
temp_file = "temp_readings.json"

# Create a new directory for the reports with current date and time
current_time = datetime.now().strftime("%Y%m%d-%H%M")
report_dir = f"{current_time}-Reports"
os.makedirs(report_dir, exist_ok=True)
psu_dir = os.path.join(report_dir, "psus")
fan_dir = os.path.join(report_dir, "fans")
temperatures_dir = os.path.join(report_dir, "temperatures")
os.makedirs(psu_dir, exist_ok=True)
os.makedirs(fan_dir, exist_ok=True)
os.makedirs(temperatures_dir, exist_ok=True)

# Set up argument parser
parser = argparse.ArgumentParser(description='Generate plots and reports from sensor data.')
parser.add_argument('--resample', type=int, default=1, help='Number of samples to skip for each sensor. Default is 1 (consider all samples).')
args = parser.parse_args()

def main():
    # Load data
    psu_df = load_data(psu_file)
    fan_df = load_data(fan_file)
    temp_df = load_data(temp_file)

    # Resample data if necessary
    if args.resample > 1:
        psu_df = psu_df.iloc[::args.resample]
        fan_df = fan_df.iloc[::args.resample]
        temp_df = temp_df.iloc[::args.resample]

    # Determine the monitoring period
    first_timestamp = min(psu_df["Timestamp"].min(), fan_df["Timestamp"].min(), temp_df["Timestamp"].min())
    last_timestamp = max(psu_df["Timestamp"].max(), fan_df["Timestamp"].max(), temp_df["Timestamp"].max())

    # Plot PSU power usage
    plot_psu_power_usage(psu_df, psu_dir)

    # Plot total PSU power breakdown
    plot_psu_breakdown(psu_df, psu_dir)

    # Plot FAN speed
    plot_fan_speed(fan_df, fan_dir)

    # Plot aggregate FAN speed
    plot_fan_aggregate(fan_df, report_dir)

    # Plot temperature data
    plot_temperature_data(temp_df, temperatures_dir)

    # Create PDF report
    create_pdf_report(first_timestamp, last_timestamp, report_dir, psu_dir, fan_dir, temperatures_dir)

    # Finalize Report
    finalize_report.finalize(f"{report_dir}/report.pdf", 
                             output_pdf=f"{report_dir}/{datetime.today().strftime('%m-%d-%Y')}_c885a_report.pdf", 
                             footer_text=f"{datetime.today().strftime('%m-%d-%Y')} - Cisco Networking, Compute Technical Marketing", 
                             logo_url="https://upload.wikimedia.org/wikipedia/commons/0/08/Cisco_logo_blue_2016.svg", 
                             logo_position="top_right", 
                             logo_scale=0.2, 
                             font_size=8, 
                             first_page_logo_position="center", 
                             first_page_logo_size="medium",
                             append_blank_page = True,  # Option to append a blank page
                             blank_page_logo_position = "center",  # Custom position for the blank page logo
                             blank_page_logo_size = "medium"  # Custom size for the blank page logo)
    )
    
    # Remove Original Report
    os.remove(f"{report_dir}/report.pdf")
if __name__ == "__main__":
    main()