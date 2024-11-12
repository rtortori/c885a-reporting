from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import grey
import requests
from PIL import Image
import io
import cairosvg
from datetime import datetime
import os

def get_logo_position(position, page_width, page_height, logo_width, logo_height, margin=10):
    positions = {
        "top_left": (margin, page_height - logo_height - margin),
        "top_right": (page_width - logo_width - margin, page_height - logo_height - margin),
        "bottom_left": (margin, margin),
        "bottom_right": (page_width - logo_width - margin, margin),
        "center": ((page_width - logo_width) / 2, (page_height - logo_height) / 2),
        "center_up": ((page_width - logo_width) / 2, page_height / 2 + logo_height)
    }
    return positions.get(position, (page_width - logo_width - margin, page_height - logo_height - margin))  # Default to top right if invalid position

def download_logo(logo_url):
    response = requests.get(logo_url)
    response.raise_for_status()
    if logo_url.lower().endswith('.svg'):
        # Convert SVG to PNG
        png_data = cairosvg.svg2png(bytestring=response.content)
        return Image.open(io.BytesIO(png_data))
    else:
        return Image.open(io.BytesIO(response.content))

def finalize(input_pdf, output_pdf="report.pdf", footer_text=None, logo_url=None, logo_position="top_right", logo_scale=1.0, font_size=12, first_page_logo_position=None, first_page_logo_size="medium", append_blank_page=False, blank_page_logo_position=None, blank_page_logo_size="medium"):
    existing_pdf = PdfReader(open(input_pdf, "rb"))
    output = PdfWriter()

    if not footer_text:
        today = datetime.today().strftime('%m-%d-%Y')
        footer_text = f"{today} - Cisco Networking, Compute Technical Marketing"

    if not logo_url:
        logo_url = "https://upload.wikimedia.org/wikipedia/commons/0/08/Cisco_logo_blue_2016.svg"

    try:
        logo = download_logo(logo_url)
    except Exception as e:
        print(f"Error downloading or processing logo: {e}")
        return

    logo_width, logo_height = logo.size
    logo_width *= logo_scale
    logo_height *= logo_scale

    first_page_logo_scales = {"small": logo_scale, "medium": logo_scale * 10, "big": logo_scale * 20}
    first_page_logo_scale = first_page_logo_scales.get(first_page_logo_size, logo_scale)
    blank_page_logo_scale = first_page_logo_scales.get(blank_page_logo_size, logo_scale)

    first_page_logo_width = logo_width * first_page_logo_scale
    first_page_logo_height = logo_height * first_page_logo_scale
    blank_page_logo_width = logo_width * blank_page_logo_scale
    blank_page_logo_height = logo_height * blank_page_logo_scale

    total_pages = len(existing_pdf.pages)
    logo_file_path = "temp_logo.png"

    for i in range(total_pages):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        page_width, page_height = letter

        # Set font size and color
        can.setFont("Helvetica", font_size)
        can.setFillColorRGB(0.75, 0.75, 0.75)  # Light grey color

        # Add page number
        can.drawString(500, 10, f"Page {i+1} / {total_pages}")

        # Add footer text
        can.drawString(30, 10, footer_text)

        # Add logo
        if i == 0 and first_page_logo_position:
            logo_x, logo_y = get_logo_position(first_page_logo_position, page_width, page_height, first_page_logo_width, first_page_logo_height)
            logo.save(logo_file_path, format="PNG")
            can.drawImage(logo_file_path, logo_x, logo_y, width=first_page_logo_width, height=first_page_logo_height, mask='auto')
        else:
            logo_x, logo_y = get_logo_position(logo_position, page_width, page_height, logo_width, logo_height)
            logo.save(logo_file_path, format="PNG")
            can.drawImage(logo_file_path, logo_x, logo_y, width=logo_width, height=logo_height, mask='auto')

        can.save()
        packet.seek(0)

        new_pdf = PdfReader(packet)
        page = existing_pdf.pages[i]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

    if append_blank_page:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        page_width, page_height = letter

        # Add logo to the blank page
        if blank_page_logo_position:
            logo_x, logo_y = get_logo_position(blank_page_logo_position, page_width, page_height, blank_page_logo_width, blank_page_logo_height)
            logo.save(logo_file_path, format="PNG")
            can.drawImage(logo_file_path, logo_x, logo_y, width=blank_page_logo_width, height=blank_page_logo_height, mask='auto')

        can.save()
        packet.seek(0)

        new_pdf = PdfReader(packet)
        blank_page = new_pdf.pages[0]
        output.add_page(blank_page)

    with open(output_pdf, "wb") as outputStream:
        output.write(outputStream)

    # Delete the temporary logo file
    if os.path.exists(logo_file_path):
        os.remove(logo_file_path)