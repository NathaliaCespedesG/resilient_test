from PyPDF2 import PdfReader, PdfMerger
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet

 

#NHS
num = 1
date = "05 July 2023"
# Create a list of data for the table
data = [
    ["Overview", "Weight", "Day \nAverage \n Heart Rate", "Sleep Average \n Heart Rate", "Sleep \n Respiration \n Rate", "Sleep \n Duration", "Nights with \n  moderate/severe \n sleep apnoe ","Steps"],
    ["Current Week", "Data 2", "Data 3", "Data 4", "Data 5", "Data 6", "Data 7", "Data 8"],
    ["Last Week", "Data 5", "Data 6","Data 5", "Data 6", "Data 4", "Data 7" , "Data 8"],
]

# Create a list of images for the matrix plot
images = [
    "HR_ScanWatchScatter.png",
    "Steps_curvedbar.png",
    "Scale.png",
    "HRScatter.png",
    "SleepMat_RR.png",
    "sleep_summary.png",
]

# Define the size and positioning of the table and images
table_width = 6 * inch
table_height = 1.7 * inch
image_width = 3.55 * inch
image_height = 2.5205 * inch
spacing = 0.5 * cm

# Create a canvas and set the size
doc = SimpleDocTemplate("output.pdf", pagesize=A4, title="Resilient")


# Function to create the title page
def create_title_page(canvas, doc):
    styles = getSampleStyleSheet()


    
    title_text = "RESILIENT: Weekly Health Report"
    title_style = styles['Title']
    title_style.alignment = 1  # Set alignment to center
    title_style.fontSize = 14 
    title = Paragraph(title_text, title_style)
    title.wrapOn(canvas, doc.width, doc.height)
    title.drawOn(canvas, doc.leftMargin, doc.height + 3 * cm )


    # Draw additional text
    text = "Participant NHS no.: " + str(num) + "                                                            "+ "W/C: "+ date
    canvas.setFont("Helvetica", 11)
    canvas.drawString(doc.leftMargin - 0.7 * cm , doc.height + 2.3 * cm, text)

# Add the title page to the document
styles = getSampleStyleSheet()
doc.build([Paragraph("", styles['Normal'])], onFirstPage=create_title_page)

# Create a table object and set its properties
table = Table(data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
    ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
]))

# Changing the font size for row 1
table_style = TableStyle([('FONTSIZE', (0, 0), (-1, 0), 11)])
table.setStyle(table_style)

# Changing the font size for column 1
for i in range(1, len(data)):
    table_style = TableStyle([('FONTSIZE', (0, i), (0, i), 11)])
    table.setStyle(table_style)

spacer = Spacer(1, spacing)

# Create a list to hold the images
image_list = []

# Add the images to the list
for image_path in images:
    image = Image(image_path, width=image_width, height=image_height)
    image_list.append(image)

# Create a table for the images in a matrix-like plot
image_table = Table([image_list[i:i+2] for i in range(0, len(image_list), 2)])

# Build the PDF document
elements = [spacer,table, spacer, image_table]
doc.build(elements)
