import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Configurable variables
tolerance_seconds = 5  # Tolerance to identify readings belonging to the same period in seconds

def load_data(file_path):
    """Load JSON data from a file and return it as a DataFrame."""
    with open(file_path, "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format='ISO8601')
    return df

def plot_temperature_data(df, temperatures_dir):
    """Generate temperature plots for different components and save them in the temperatures directory."""

    # Ensure the temperatures directory exists
    os.makedirs(temperatures_dir, exist_ok=True)

    # Helper function to create and save plots
    def create_plot(temp_df, title, file_name):
        plt.figure(figsize=(10, 6))
        for name in temp_df["Name"].unique():
            plt.plot(temp_df[temp_df["Name"] == name]["Timestamp"], temp_df[temp_df["Name"] == name]["Reading"], label=name)
        plt.xlabel("Timestamp")
        plt.ylabel("Temperature (°C)")
        plt.title(title)
        plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        plt.gcf().autofmt_xdate()  # Rotate timestamp labels to vertical
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))  # Place legend outside the plot area
        plt.grid(True)
        plt.savefig(os.path.join(temperatures_dir, file_name), bbox_inches='tight', dpi=300)
        plt.close()

    # Plot CPU Tray PSUs Temperatures
    cpu_tray_psu_df = df[df["Name"].str.startswith("TEMP_CPU_TRAY_PSU")]
    create_plot(cpu_tray_psu_df, "CPU Tray PSUs Temperatures", "temp_cpu_tray_psus.png")

    # Plot GPU Tray PSUs Temperatures
    gpu_tray_psu_df = df[df["Name"].str.startswith("TEMP_GPU_TRAY_PSU")]
    create_plot(gpu_tray_psu_df, "GPU Tray PSUs Temperatures", "temp_gpu_tray_psus.png")

    # Plot Memory Temperatures
    dimm_zone_df = df[df["Name"].str.startswith("TEMP_DIMM_ZONE")]
    create_plot(dimm_zone_df, "Memory Temperatures (DIMM Zones)", "temp_dimm_zones.png")

    # Plot GPU Temperatures
    gpu_df = df[df["Name"].str.startswith("TEMP_GB_GPU")]
    create_plot(gpu_df, "GPU Temperatures", "temp_gpus.png")

    # Plot NVME Drives Temperatures
    nvme_df = df[df["Name"].str.startswith("TEMP_NVME")]
    create_plot(nvme_df, "NVME Drives Temperatures", "temp_nvmes.png")

    # Plot Ambient Temperature
    ambient_df = df[df["Name"] == "TEMP_AMBIENT"]
    create_plot(ambient_df, "Ambient Temperature", "temp_ambient.png")

def plot_psu_power_usage(df, psu_dir):
    """Plot each PSU power usage over time and the total power usage."""
    gpu_psu_list = df[df["Name"].str.startswith("GPU_TRAY_PSU")]["Name"].unique()
    cpu_psu_list = df[df["Name"].str.startswith("CPU_TRAY_PSU")]["Name"].unique()
    total_power_df = df[df["Name"] == "Total Power in W"]

    # Plot each GPU Tray PSU power usage
    for psu in gpu_psu_list:
        psu_df = df[df["Name"] == psu]
        plt.figure(figsize=(10, 6))
        plt.plot(psu_df["Timestamp"], psu_df["Reading"], label=psu)
        plt.xlabel("Timestamp")
        plt.ylabel("Power Usage (W)")
        plt.title(f"{psu} Power Usage in Watts")
        plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        plt.gcf().autofmt_xdate()  # Rotate timestamp labels to vertical
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(psu_dir, f"{psu.lower()}_power_usage.png"), dpi=300)
        plt.close()

    # Plot each CPU Tray PSU power usage
    for psu in cpu_psu_list:
        psu_df = df[df["Name"] == psu]
        plt.figure(figsize=(10, 6))
        plt.plot(psu_df["Timestamp"], psu_df["Reading"], label=psu)
        plt.xlabel("Timestamp")
        plt.ylabel("Power Usage (W)")
        plt.title(f"{psu} Power Usage in Watts")
        plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        plt.gcf().autofmt_xdate()  # Rotate timestamp labels to vertical
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(psu_dir, f"{psu.lower()}_power_usage.png"), dpi=300)
        plt.close()

    # Plot total PSU power usage
    plt.figure(figsize=(10, 6))
    plt.plot(total_power_df["Timestamp"], total_power_df["Reading"], label="Total Power")
    plt.xlabel("Timestamp")
    plt.ylabel("Power Usage (W)")
    plt.title("Total PSU Power Usage in Watts")
    plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
    plt.gcf().autofmt_xdate()  # Rotate timestamp labels to vertical
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(psu_dir, "total_psu_power_usage.png"), dpi=300)
    plt.close()

def plot_psu_breakdown(df, psu_dir):
    """Plot total PSU power usage with a breakdown of each PSU's contribution."""
    df = df[(df["Name"] != "Total Power in W") & (df["Name"].str.startswith("GPU_TRAY_PSU") | df["Name"].str.startswith("CPU_TRAY_PSU"))].copy()  # Create a copy to avoid setting values on a slice
    df["Batch"] = (df["Timestamp"].diff().dt.total_seconds() > tolerance_seconds).cumsum()
    df.set_index(["Batch", "Timestamp"], inplace=True)
    df = df.pivot(columns="Name", values="Reading")

    # Sum PSU readings for each batch
    batch_sums = df.groupby(level="Batch").sum()

    # Create a stacked histogram with larger width
    ax = batch_sums.plot(kind="bar", stacked=True, figsize=(13, 6))  # 30% wider than original 10
    ax.set_xlabel("")  # Remove X-axis label
    ax.set_ylabel("Power Usage (W)")
    ax.set_title("Total PSU Power Usage Breakdown")
    ax.legend().set_visible(False)  # Hide the legend
    plt.gcf().autofmt_xdate()  # Rotate timestamp labels to vertical
    plt.savefig(os.path.join(psu_dir, "total_psu_power_breakdown.png"), bbox_inches='tight', dpi=300)
    plt.close()

def plot_fan_speed(df, fan_dir):
    """Plot each FAN speed over time, combining Front and Rear rotors."""
    fan_list = df["Name"].unique()
    combined_fan_list = sorted(set(fan.split(' ')[0] for fan in fan_list))

    for fan in combined_fan_list:
        front_fan_name = f"{fan} Front"
        rear_fan_name = f"{fan} Rear"
        front_fan_df = df[df["Name"] == front_fan_name]
        rear_fan_df = df[df["Name"] == rear_fan_name]
        
        plt.figure(figsize=(10, 6))
        if not front_fan_df.empty:
            plt.plot(front_fan_df["Timestamp"], front_fan_df["Reading"], label=f"{fan} Front")
        if not rear_fan_df.empty:
            plt.plot(rear_fan_df["Timestamp"], rear_fan_df["Reading"], label=f"{fan} Rear")
        plt.xlabel("Timestamp")
        plt.ylabel("Speed (RPM)")
        plt.title(f"FAN {fan} Speed in RPM")
        plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        plt.gcf().autofmt_xdate()  # Rotate timestamp labels to vertical
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(fan_dir, f"fan_{fan}_speed.png"), dpi=300)
        plt.close()

def plot_fan_aggregate(df, report_dir):
    """Plot aggregate data of all FANs over time."""
    plt.figure(figsize=(10, 6))

    # Plot FANs
    fan_list = df["Name"].unique()
    for fan in fan_list:
        fan_df = df[df["Name"] == fan]
        plt.plot(fan_df["Timestamp"], fan_df["Reading"], label=fan)

    plt.xlabel("Timestamp")
    plt.ylabel("Speed (RPM)")
    plt.title("Aggregate FAN Speed Over Time")
    plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
    plt.gcf().autofmt_xdate()  # Rotate timestamp labels to vertical
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))  # Place legend outside the plot area
    plt.grid(True)
    plt.savefig(os.path.join(report_dir, "fans/aggregate_fan_speed.png"), bbox_inches='tight', dpi=300)
    plt.close()

def create_table_of_contents(c, sections):
    """Create a table of contents with clickable links."""
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 750, "Table of Contents")
    c.setFont("Helvetica", 12)
    y_position = 700
    for section in sections:
        c.drawString(40, y_position, section[0])
        c.linkRect("", section[1], (40, y_position, 550, y_position + 20))
        y_position -= 20
    c.showPage()

def create_pdf_report(first_timestamp, last_timestamp, report_dir, psu_dir, fan_dir, temperatures_dir):
    """Create a PDF report including all plots with descriptions."""
    pdf_path = os.path.join(report_dir, "report.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Title Page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height - 100, "Cisco UCS C885A")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2.0, height - 130, "FANs, Temperatures and Power Utilization")
    c.setFont("Helvetica", 12)
    subtitle = f"Monitoring period: from {first_timestamp.strftime('%d-%B-%Y - %H:%M:%S')} to {last_timestamp.strftime('%d-%B-%Y - %H:%M:%S')} - UTC"
    c.drawCentredString(width / 2.0, height - 170, subtitle)
    c.showPage()

    # Table of Contents
    sections = [
        ("1. PSUs", "PSUs"),
        ("  1.1 Total Power", "Total_Power"),
        #("  1.2 Breakdown", "Breakdown"),
        ("  1.2 GPU Tray PSU Usage", "GPU_Tray_PSU_Usage"),
        ("  1.3 CPU Tray PSU Usage", "CPU_Tray_PSU_Usage"),
        ("2. FANs", "FANs"),
        ("  2.1 GPU Tray System FANs", "GPU_Tray_System_FANs"),
        ("  2.2 CPU Tray System FANs", "CPU_Tray_System_FANs"),
        ("  2.3 SSD System FANs", "SSD_System_FANs"),
        ("  2.4 Aggregate FAN Speed", "Aggregate_FAN_Speed"),
        ("3. Temperatures", "Temperatures"),
        ("  3.1 Ambient Temperature", "Ambient_Temperature"),
        ("  3.2 CPU Tray Temperatures", "CPU_Tray_Temperatures"),
        ("  3.3 GPU Tray Temperatures", "GPU_Tray_Temperatures"),
        ("  3.4 GPUs Temperatures", "GPUs_Temperatures"),
        ("  3.5 Memory Temperatures", "Memory_Temperatures"),
        ("  3.6 NVME Disks Temperatures", "NVME_Disks_Temperatures")
    ]
    create_table_of_contents(c, sections)

    # PSU Section
    c.bookmarkPage("PSUs")
    c.addOutlineEntry("1. PSUs", "PSUs", level=0)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 50, "1. PSUs")
    c.setFont("Helvetica", 12)

    c.bookmarkPage("Total_Power")
    c.addOutlineEntry("1.1 Total Power", "Total_Power", level=1)
    c.drawString(40, height - 80, "1.1 Total Power")
    img_path = os.path.join(psu_dir, "total_psu_power_usage.png")
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        width_needed = (width - 80) * 0.75  # Absolute 75% scale
        height_needed = width_needed * aspect
        c.drawImage(img, 40, height - 80 - height_needed - 20, width_needed, height_needed)
    else:
        c.drawString(40, height - 110, "Total Power plot not found.")
    c.showPage()

    #c.bookmarkPage("Breakdown")
    #c.addOutlineEntry("1.2 Breakdown", "Breakdown", level=1)
    #c.drawString(40, height - 50, "1.2 Breakdown")
    #img_path = os.path.join(psu_dir, "total_psu_power_breakdown.png")
    #if os.path.exists(img_path):
    #    img = ImageReader(img_path)
    #    img_width, img_height = img.getSize()
    #    aspect = img_height / float(img_width)
    #    width_needed = (width - 80) * 0.75  # Absolute 75% scale
    #    height_needed = width_needed * aspect
    #    c.drawImage(img, 40, height - 50 - height_needed - 20, width_needed, height_needed)
    #else:
    #    c.drawString(40, height - 110, "Breakdown plot not found.")
    #c.showPage()

    # GPU Tray PSU Usage
    c.bookmarkPage("GPU_Tray_PSU_Usage")
    c.addOutlineEntry("1.2 GPU Tray PSU Usage", "GPU_Tray_PSU_Usage", level=1)
    c.drawString(40, height - 50, "1.2 GPU Tray PSU Usage")
    c.setFont("Helvetica", 12)
    gpu_psu_files = sorted([f for f in os.listdir(psu_dir) if f.startswith("gpu_tray_psu") and f.endswith(".png")], key=lambda x: int(x.split('_')[2][3]))
    if not gpu_psu_files:
        c.drawString(40, height - 80, "No GPU Tray PSU plots found.")
    current_plot = 1
    y_position = height - 80
    for psu_file in gpu_psu_files:
        psu_number = psu_file.split('_')[2][3]
        if current_plot % 2 == 1 and current_plot != 1:
            c.showPage()
            y_position = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_position, f"1.2.{current_plot} - GPU Tray PSU {psu_number} Power Usage in Watts")
        img_path = os.path.join(psu_dir, psu_file)
        if os.path.exists(img_path):
            img = ImageReader(img_path)
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            width_needed = (width - 80) * 0.75  # Absolute 75% scale
            height_needed = width_needed * aspect
            c.drawImage(img, 40, y_position - height_needed - 20, width_needed, height_needed)
            y_position -= height_needed + 40
        else:
            c.drawString(40, y_position - 20, f"Plot {psu_file} not found.")
        current_plot += 1
    c.showPage()

    # CPU Tray PSU Usage
    c.bookmarkPage("CPU_Tray_PSU_Usage")
    c.addOutlineEntry("1.3 CPU Tray PSU Usage", "CPU_Tray_PSU_Usage", level=1)
    c.drawString(40, height - 50, "1.3 CPU Tray PSU Usage")
    c.setFont("Helvetica", 12)
    cpu_psu_files = sorted([f for f in os.listdir(psu_dir) if f.startswith("cpu_tray_psu") and f.endswith(".png")], key=lambda x: int(x.split('_')[2][3]))
    if not cpu_psu_files:
        c.drawString(40, height - 80, "No CPU Tray PSU plots found.")
    current_plot = 1
    y_position = height - 80
    for psu_file in cpu_psu_files:
        psu_number = psu_file.split('_')[2][3]
        if current_plot % 2 == 1 and current_plot != 1:
            c.showPage()
            y_position = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_position, f"1.3.{current_plot} - CPU Tray PSU {psu_number} Power Usage in Watts")
        img_path = os.path.join(psu_dir, psu_file)
        if os.path.exists(img_path):
            img = ImageReader(img_path)
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            width_needed = (width - 80) * 0.75  # Absolute 75% scale
            height_needed = width_needed * aspect
            c.drawImage(img, 40, y_position - height_needed - 20, width_needed, height_needed)
            y_position -= height_needed + 40
        else:
            c.drawString(40, y_position - 20, f"Plot {psu_file} not found.")
        current_plot += 1
    c.showPage()

    # FANs Section
    c.bookmarkPage("FANs")
    c.addOutlineEntry("2. FANs", "FANs", level=0)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 50, "2. FANs")
    c.setFont("Helvetica", 12)

    # GPU Tray System FANs
    c.bookmarkPage("GPU_Tray_System_FANs")
    c.addOutlineEntry("2.1 GPU Tray System FANs", "GPU_Tray_System_FANs", level=1)
    c.drawString(40, height - 80, "2.1 GPU Tray System FANs")
    gpu_tray_fan_files = sorted([f for f in os.listdir(fan_dir) if "FAN" in f and int(f.split('_')[1].split()[0][3:]) in range(1, 9)], key=lambda x: int(x.split('_')[1].split()[0][3:]))
    if not gpu_tray_fan_files:
        c.drawString(40, height - 110, "No GPU Tray System FAN plots found.")
    current_plot = 1
    y_position = height - 110
    for fan_file in gpu_tray_fan_files:
        fan_name = fan_file.split('_')[1].split()[0]
        if current_plot % 2 == 1 and current_plot != 1:
            c.showPage()
            y_position = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_position, f"2.1.{current_plot} - GPU Tray System FAN {fan_name} Speed in RPM")
        img_path = os.path.join(fan_dir, fan_file)
        if os.path.exists(img_path):
            img = ImageReader(img_path)
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            width_needed = (width - 80) * 0.75  # Absolute 75% scale
            height_needed = width_needed * aspect
            c.drawImage(img, 40, y_position - height_needed - 20, width_needed, height_needed)
            y_position -= height_needed + 40
        else:
            c.drawString(40, y_position - 20, f"Plot {fan_file} not found.")
        current_plot += 1
    c.showPage()

    # CPU Tray System FANs
    c.bookmarkPage("CPU_Tray_System_FANs")
    c.addOutlineEntry("2.2 CPU Tray System FANs", "CPU_Tray_System_FANs", level=1)
    c.drawString(40, height - 80, "2.2 CPU Tray System FANs")
    cpu_tray_fan_files = sorted([f for f in os.listdir(fan_dir) if "FAN" in f and int(f.split('_')[1].split()[0][3:]) in range(9, 13)], key=lambda x: int(x.split('_')[1].split()[0][3:]))
    if not cpu_tray_fan_files:
        c.drawString(40, height - 110, "No CPU Tray System FAN plots found.")
    current_plot = 1
    y_position = height - 110
    for fan_file in cpu_tray_fan_files:
        fan_name = fan_file.split('_')[1].split()[0]
        if current_plot % 2 == 1 and current_plot != 1:
            c.showPage()
            y_position = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_position, f"2.2.{current_plot} - CPU Tray System FAN {fan_name} Speed in RPM")
        img_path = os.path.join(fan_dir, fan_file)
        if os.path.exists(img_path):
            img = ImageReader(img_path)
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            width_needed = (width - 80) * 0.75  # Absolute 75% scale
            height_needed = width_needed * aspect
            c.drawImage(img, 40, y_position - height_needed - 20, width_needed, height_needed)
            y_position -= height_needed + 40
        else:
            c.drawString(40, y_position - 20, f"Plot {fan_file} not found.")
        current_plot += 1
    c.showPage()

    # SSD System FANs
    c.bookmarkPage("SSD_System_FANs")
    c.addOutlineEntry("2.3 SSD System FANs", "SSD_System_FANs", level=1)
    c.drawString(40, height - 80, "2.3 SSD System FANs")
    ssd_tray_fan_files = sorted([f for f in os.listdir(fan_dir) if "FAN" in f and int(f.split('_')[1].split()[0][3:]) in range(13, 17)], key=lambda x: int(x.split('_')[1].split()[0][3:]))
    if not ssd_tray_fan_files:
        c.drawString(40, height - 110, "No SSD System FAN plots found.")
    current_plot = 1
    y_position = height - 110
    for fan_file in ssd_tray_fan_files:
        fan_name = fan_file.split('_')[1].split()[0]
        if current_plot % 2 == 1 and current_plot != 1:
            c.showPage()
            y_position =  height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_position, f"2.3.{current_plot} - SSD System FAN {fan_name} Speed in RPM")
        img_path = os.path.join(fan_dir, fan_file)
        if os.path.exists(img_path):
            img = ImageReader(img_path)
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            width_needed = (width - 80) * 0.75  # Absolute 75% scale
            height_needed = width_needed * aspect
            c.drawImage(img, 40, y_position - height_needed - 20, width_needed, height_needed)
            y_position -= height_needed + 40
        else:
            c.drawString(40, y_position - 20, f"Plot {fan_file} not found.")
        current_plot += 1
    c.showPage()

    # Aggregate FAN Speed
    c.bookmarkPage("Aggregate_FAN_Speed")
    c.addOutlineEntry("2.4 Aggregate FAN Speed", "Aggregate_FAN_Speed", level=1)
    c.drawString(40, height - 80, "2.4 Aggregate FAN Speed")
    img_path = os.path.join(report_dir, "fans/aggregate_fan_speed.png")
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        width_needed = (width - 80) * 0.75  # Absolute 75% scale
        height_needed = width_needed * aspect
        c.drawImage(img, 40, height - 80 - height_needed - 20, width_needed, height_needed)
    else:
        c.drawString(40, height - 110, "Aggregate FAN Speed plot not found.")
    c.showPage()

    # Temperatures Section
    c.bookmarkPage("Temperatures")
    c.addOutlineEntry("3. Temperatures", "Temperatures", level=0)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 50, "3. Temperatures")
    c.setFont("Helvetica", 12)

    # Ambient Temperature
    c.bookmarkPage("Ambient_Temperature")
    c.addOutlineEntry("3.1 Ambient Temperature", "Ambient_Temperature", level=1)
    c.drawString(40, height - 80, "3.1 Ambient Temperature")
    img_path = os.path.join(temperatures_dir, "temp_ambient.png")
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        width_needed = (width - 80) * 0.75  # Absolute 75% scale
        height_needed = width_needed * aspect
        c.drawImage(img, 40, height - 80 - height_needed - 20, width_needed, height_needed)
    else:
        c.drawString(40, height - 110, "Ambient Temperature plot not found.")
    c.showPage()

    # CPU Tray Temperatures
    c.bookmarkPage("CPU_Tray_Temperatures")
    c.addOutlineEntry("3.2 CPU Tray Temperatures", "CPU_Tray_Temperatures", level=1)
    c.drawString(40, height - 50, "3.2 CPU Tray Temperatures")
    img_path = os.path.join(temperatures_dir, "temp_cpu_tray_psus.png")
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        width_needed = (width - 80) * 0.75  # Absolute 75% scale
        height_needed = width_needed * aspect
        c.drawImage(img, 40, height - 80 - height_needed - 20, width_needed, height_needed)
    else:
        c.drawString(40, height - 110, "CPU Tray Temperatures plot not found.")
    c.showPage()

    # GPU Tray Temperatures
    c.bookmarkPage("GPU_Tray_Temperatures")
    c.addOutlineEntry("3.3 GPU Tray Temperatures", "GPU_Tray_Temperatures", level=1)
    c.drawString(40, height - 50, "3.3 GPU Tray Temperatures")
    img_path = os.path.join(temperatures_dir, "temp_gpu_tray_psus.png")
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        width_needed = (width - 80) * 0.75  # Absolute 75% scale
        height_needed = width_needed * aspect
        c.drawImage(img, 40, height - 80 - height_needed - 20, width_needed, height_needed)
    else:
        c.drawString(40, height - 110, "GPU Tray Temperatures plot not found.")
    c.showPage()

    # GPUs Temperatures
    c.bookmarkPage("GPUs_Temperatures")
    c.addOutlineEntry("3.4 GPUs Temperatures", "GPUs_Temperatures", level=1)
    c.drawString(40, height - 50, "3.4 GPUs Temperatures")
    img_path = os.path.join(temperatures_dir, "temp_gpus.png")
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        width_needed = (width - 80) * 0.75  # Absolute 75% scale
        height_needed = width_needed * aspect
        c.drawImage(img, 40, height - 80 - height_needed - 20, width_needed, height_needed)
    else:
        c.drawString(40, height - 110, "GPUs Temperatures plot not found.")
    c.showPage()

    # Memory Temperatures
    c.bookmarkPage("Memory_Temperatures")
    c.addOutlineEntry("3.5 Memory Temperatures", "Memory_Temperatures", level=1)
    c.drawString(40, height - 50, "3.5 Memory Temperatures")
    img_path = os.path.join(temperatures_dir, "temp_dimm_zones.png")
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        width_needed = (width - 80) * 0.75  # Absolute 75% scale
        height_needed = width_needed * aspect
        c.drawImage(img, 40, height - 80 - height_needed - 20, width_needed, height_needed)
    else:
        c.drawString(40, height - 110, "Memory Temperatures plot not found.")
    c.showPage()

    # NVME Disks Temperatures
    c.bookmarkPage("NVME_Disks_Temperatures")
    c.addOutlineEntry("3.6 NVME Disks Temperatures", "NVME_Disks_Temperatures", level=1)
    c.drawString(40, height - 50, "3.6 NVME Disks Temperatures")
    img_path = os.path.join(temperatures_dir, "temp_nvmes.png")
    if os.path.exists(img_path):
        img = ImageReader(img_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)
        width_needed = (width - 80) * 0.75  # Absolute 75% scale
        height_needed = width_needed * aspect
        c.drawImage(img, 40, height - 80 - height_needed - 20, width_needed, height_needed)
    else:
        c.drawString(40, height - 110, "NVME Disks Temperatures plot not found.")
    c.showPage()

    c.save()