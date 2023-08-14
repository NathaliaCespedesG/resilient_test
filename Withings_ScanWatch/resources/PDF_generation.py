from PyPDF2 import PdfReader, PdfMerger
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet
import math
import numpy as np



class PDF_generation(object):

	def __init__(self, day_hr: None, 
					night_hr: None, 
					night_rr: None,
					steps: None, 
					sleep_duration: None, 
					sleep_apnoea: None,
					weight: None,
					c_date : None,
					e_date: None,
					path: None

					):


		#creating the database object
		self.path = path
		print('path', self.path)
		# Values for building the table
		self.day_hr = day_hr
		self.night_hr = night_hr
		self.night_rr = night_rr
		self.steps = steps
		self.sleep_duration = sleep_duration
		self.sleep_apnoea = sleep_apnoea
		self.weight = weight
		self.c_date = c_date
		self.e_date = e_date
		#NHS
		self.id = '000p'

		self.document_generation()

	# Function to create the title page

	def averages_data(self, val1, val2):

		val1 = np.array(val1, dtype=float)
		val1[np.isnan(val1)] = np.nan

		val2 = np.array(val2, dtype=float)
		val2[np.isnan(val2)] = np.nan


		if val1 == [] or (np.all(np.isnan(val1))) or (np.all(val1==0)):
			self.mean_val1 = 'N/A'
			self.sd_val1 = ''
			self.var_1 = self.mean_val1
		else:

			val1 = [value for value in val1 if value is not None and value != 0 and not math.isnan(value)]
			self.mean_val1 = (np.mean(val1))
			self.mean_val1 = str("{:.2f}".format(self.mean_val1))
			self.sd_val1 = (np.std(val1))
			self.sd_val1 = str("{:.1f}".format(self.sd_val1))
			self.var_1 = self.mean_val1 + " ± "+ self.sd_val1


		if val2 == [] or (np.all(np.isnan(val2))) or (np.all(val2==0)):
			self.mean_val2 = 'N/A'
			self.sd_val2 = ''
			self.var_2 = self.mean_val2

		else:
			val2 = [value for value in val2 if value is not None and value != 0 and not math.isnan(value)]
			self.mean_val2 = (np.mean(val2))
			self.mean_val2 = str("{:.2f}".format(self.mean_val2))
			self.sd_val2 = (np.std(val2))
			self.sd_val2 = str("{:.1f}".format(self.sd_val2))
			self.var_2 = self.mean_val2 + " ± "+ self.sd_val2

		return(self.var_1, self.var_2)


	def average_steps(self, val1, val2):

		if val1 == [] or (np.all(np.isnan(np.array(val1)))) or (np.all(np.array(val1)==0)):
			self.mean_val1 = 'N/A'
			self.sd_val1 = ''
			self.var_1 = self.mean_val1
		else:

			val1 = [value for value in val1 if value is not None and value != 0 and not math.isnan(value)]
			self.mean_val1 = (np.mean(val1))
			self.mean_val1 = str(int(self.mean_val1))
			self.sd_val1 = (np.std(val1))
			self.sd_val1 = str(int(self.sd_val1))
			self.var_1 = self.mean_val1 + " ± "+ self.sd_val1


		if val2 == [] or (np.all(np.isnan(np.array(val2)))) or (np.all(np.array(val2)==0)):
			self.mean_val2 = 'N/A'
			self.sd_val2 = ''
			self.var_2 = self.mean_val2

		else:
			val2 = [value for value in val2 if value is not None and value != 0 and not math.isnan(value)]
			self.mean_val2 = (np.mean(val2))
			self.mean_val2 = str(int(self.mean_val2))
			self.sd_val2 = (np.std(val2))

			self.sd_val2 = str(int(self.sd_val2))
			self.var_2 = self.mean_val2 + " ± "+ self.sd_val2

		return(self.var_1, self.var_2)


	def sd_comparisson(self, val1, val2, col, row):

		highlight_styles = []

		val1 = [value for value in val1 if value is not None and value != 0 and not math.isnan(value)]
		val2 = [value for value in val2 if value is not None and value != 0 and not math.isnan(value)]

		# Comparison with 1 SD difference

		if (np.mean(val1)) >= (np.mean(val2) + (2 * np.std(val2))):
			highlight_styles.append(('BACKGROUND', (col, row), (col, row), colors.lightsalmon))
		if np.mean(val1) <= np.mean(val2) - 2 * np.std(val2):
			highlight_styles.append(('BACKGROUND', (col, row), (col, row), colors.lightsalmon))
		if (np.mean(val1)) >= (np.mean(val2) + (1 * np.std(val2))):
			highlight_styles.append(('BACKGROUND', (col, row), (col, row), colors.gold))
		if np.mean(val1) <= ((np.mean(val2)) - (1 * np.std(val2))):
			highlight_styles.append(('BACKGROUND', (col, row), (col, row), colors.gold))


		return(highlight_styles)


	def conditional_highlighting(self,val1, val2, val3, val4,val5, val6, val7):

		highlight_styles = []

		dayhr_highlight = self.sd_comparisson(val1[0],val1[1], row = 1, col = 1)
		nighthr_highlight = self.sd_comparisson(val2[0],val2[1], row = 1, col = 2)
		nightrr_highlight = self.sd_comparisson(val3[0],val3[1], row = 1, col = 3)
		steps_highlight = self.sd_comparisson(val4[0],val4[1], row = 1, col = 4)
		sleepdur_highlight = self.sd_comparisson(val5[0],val5[1], row = 1, col = 5)
		sleepap_hightlight = self.sd_comparisson(val6[0],val6[1], row = 1, col = 6)
		weight_highlight = self.sd_comparisson(val7[0],val7[1], row = 1, col = 7)
	
		highlight_styles = (dayhr_highlight + nighthr_highlight + nightrr_highlight + steps_highlight + sleepdur_highlight + sleepap_hightlight +weight_highlight)

		return(highlight_styles)


	def create_title_page(self, canvas, doc):
		styles = getSampleStyleSheet()

		# Add the watermark image
		watermark_image = Image("sabp.jpg", width = 10*cm, height = 7*cm)
		watermark_image.drawOn(canvas, doc.leftMargin - 2.6*cm , doc.height + 2.2*cm)


		title_text = "RESILIENT: Weekly Health Report"
		title_style = styles['Title']
		title_style.alignment = 1  # Set alignment to center
		title_style.fontSize = 14 
		title = Paragraph(title_text, title_style)
		title.wrapOn(canvas, doc.width, doc.height)
		title.drawOn(canvas, doc.leftMargin, doc.height + 3 * cm )

		# Draw additional text
		text = "Study ID: " + self.id + "                           "+ "Date: "+ self.c_date +" - "+ self.e_date 
		canvas.setFont("Helvetica", 12)
		canvas.drawString(doc.leftMargin + 8 * cm , doc.height + 2.3 * cm, text)



	def document_generation(self):


		# Path where saving the reports

		
		document_file = self.path + "/"+ "report.pdf"
		
		# Data for the table

		hr_c, hr_p = self.averages_data(self.day_hr[0],self.day_hr[1])
		nhr_c, nhr_p = self.averages_data(self.night_hr[0],self.night_hr[1])
		rr_c, rr_p = self.averages_data(self.night_rr[0],self.night_rr[1])
		steps_c, steps_p = self.average_steps(self.steps[0],self.steps[1])
		sd_c,sd_p = self.averages_data(self.sleep_duration[0],self.sleep_duration[1])
		sa_c,sa_p  = self.averages_data(self.sleep_apnoea[0],self.sleep_apnoea[1])
		w_c, w_p = self.averages_data(self.weight[0], self.weight[1])


		# Create a list of data for the table
		data = [
    	["Overview", "Day Heart \n  Rate \n [bpm]", "Sleep \n Heart Rate \n [bpm]", "Sleep \n Respiration \n Rate", "Steps",  "Weight \n [kg]", "Sleep \n Duration \n [hours]", " Sleep \n Apnoea Index \n [breathing  \n disturbances] "],
    	["Current Week \n [av ± sd] ",hr_c , nhr_c , rr_c , steps_c, w_c , sd_c , sa_c],
    	["Last Week \n [av ± sd] ",hr_p , nhr_p  ,rr_p , steps_p , w_p , sd_p  , sa_p],
				]

		# Create a list of images for the matrix plot
		images = [
    		"HR_ScanWatchScatter.png",
    		"HRScatter.png",
    		"RRScatter.png",
    		"Steps_curvedbar.png",
    		"Scale.png",
    		"sleep_summary.png",
			]

		# Define the size and positioning of the table and images
		table_width = 6 * inch
		table_height = 1.68 * inch
		image_width = 3.5 * inch
		image_height = 2.45 * inch
		spacing = 0.3 * cm

		# Create a canvas and set the size
		doc = SimpleDocTemplate(document_file, pagesize = A4, title="Resilient")

		# Add the title page to the document
		styles = getSampleStyleSheet()
		doc.build([Paragraph("", styles['Normal'])], onFirstPage=self.create_title_page)

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
		table_style = TableStyle([('FONTSIZE', (0, 0), (-1, 0), 10)])
		table.setStyle(table_style)


		# Changing the font size for column 1
		for i in range(1, len(data)):
			table_style = TableStyle([('FONTSIZE', (0, i), (0, i), 10)])
			table.setStyle(table_style)


		#conditionals for the table
		m = self.conditional_highlighting(self.day_hr, self.night_hr, self.night_rr,
										  self.steps, self.sleep_duration, self.sleep_apnoea,
										  self.weight)
		highlight_table_style = TableStyle(m)
		table.setStyle(highlight_table_style)

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


'''
M = PDF_generation(day_hr = None, 
					night_hr = None, 
					night_rr = None,
					steps = None, 
					sleep_duration = None, 
					sleep_apnoea =None,
					weight = None,)



'''