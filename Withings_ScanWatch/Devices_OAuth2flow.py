import sys
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from withings_api import WithingsAuth, WithingsApi, AuthScope
from withings_api.common import GetSleepField, GetSleepSummaryField, get_measure_value, MeasureType, CredentialsType, MeasureGetActivityResponse, AuthFailedException
import arrow
import time
import numpy as np



#To save users credential and update refresh the token

import argparse
import os
from os import path
import pickle
from typing import cast
from urllib import parse
from typing_extensions import Final

# Database libraries to save Users' data 


import pandas as pd 
import db.database as database


# Graphics
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import timedelta, datetime
import seaborn as sns
import itertools
import matplotlib.patches as patches


#PDF files

from PyPDF2 import PdfWriter, PageObject, PdfReader
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


#This code is an adaptation of the following repository: https://github.com/vangorra/python_withings_api
#With libraries and methods modified.


# IMPORTANT!
# Create the developer account: https://developer.withings.com/developer-guide/v3/integration-guide/advanced-research-api/developer-account/create-your-accesses-no-medical-cloud


# This class is for making the authorization procedures and the OAuth2 flow
# Please refer to the following pages to have a greater understanding :
# https://developer.withings.com/developer-guide/v3/integration-guide/advanced-research-api/get-access/oauth-web-flow
# Access and refresh tokens : https://developer.withings.com/developer-guide/v3/integration-guide/advanced-research-api/get-access/access-and-refresh-tokens



class Devices_OAuth2flow(object):

	def __init__(self, client_id: None, 
					   costumer_secret: None, 
					   callback_uri: None):


		# Creating the database objective

		self.database = database.General()


		# Inputs: client_id, consumer_secret, callback_uri
		# Take into account that this inputs will be created after you
		# create your developer account

		self.client_id = client_id
		self.costumer_secret = costumer_secret
		self.callback_uri = callback_uri

		#Create the credentials File
		# This file has the authorization and refresh token which are
		# used to acquire the data fromo Withings server 
		self.CREDENTIALS_FILE: Final = path.abspath(
			path.join(path.dirname(path.abspath(__file__)), "../.credentials"))

		#Create an ID for each user

		id_user = input('Please provide the id for the user: ')

		self.database.register(user = id_user)




	def create_auth_url(self):

		# This function is to create the URL which will be used by the
		# user to authorize the acquisition of the data		 

		self.auth = WithingsAuth(

			client_id = str(self.client_id),
			consumer_secret= str(self.costumer_secret),
			callback_uri = str(self.callback_uri),

			scope=(
				AuthScope.USER_ACTIVITY,
				AuthScope.USER_METRICS,
				AuthScope.USER_INFO,
				AuthScope.USER_SLEEP_EVENTS,
				AuthScope.USER_RAW_DATA,
				)
			)

		self.authorize_url = self.auth.get_authorize_url()




	def get_user_credentials(self):

		#Depending if the device is already registered and has credentials an authorization
		#either an authorization token can be generated (for new devices) or the refresh token
		#can be used if data is requested (and 3 hours have passed after the last call)

		if path.isfile(self.CREDENTIALS_FILE):
			print("Attempting to load credentials from:", self.CREDENTIALS_FILE)
			self.api = WithingsApi(self.load_credentials(), refresh_cb = self.save_credentials)
			try:
				self.api.user_get_device()
			except MissingTokenError:
				os.remove(self.CREDENTIALS_FILE)
				print("Credentials in file are expired. Re-starting auth procedure...")
			except AuthFailedException:
				print('Im here AuthFailedException')

				#m = self.load_credentials() 
				#auth_token = m.refresh_token


				

		if not path.isfile(self.CREDENTIALS_FILE):

			print("Attempting to get credentials...")
			auth = self.create_auth_url()


			print("Goto this URL in your browser and authorize:", self.authorize_url)
			print("Once you are redirected, copy and paste the whole url"
		        "(including code) here."
		     )

			redirected_uri: Final = input("Provide the entire redirect uri: ")

			redirected_uri_params: Final = dict(
				parse.parse_qsl(parse.urlsplit(redirected_uri).query)
				)

			self.auth_code: Final = redirected_uri_params["code"]
			print("Getting credentials with auth code", self.auth_code)
			self.save_credentials(self.auth.get_credentials(self.auth_code))
			self.api = WithingsApi(self.load_credentials(), refresh_cb = self.save_credentials)

		orig_access_token = self.api.get_credentials().access_token
		print("Refreshing token...")
		self.api.refresh_token()
		print("After Refreshing")
		print( 'UserID', self.api.get_credentials().userid )
		#assert orig_access_token != api.get_credentials().access_token

			
	


	def devices_info(self):

		# This function generates the device information. For instance, the hash_deviceid,
		# battery levels, serial number, device_id, among others. Some of this parameters
		# are used in other services to activate functions.

		devices = self.api.user_get_device()
		devices = devices['devices']
		#print(devices)
		type_d = [i['type'] for i in devices]
		hash_deviceid = [i['hash_deviceid'] for i in devices]
		MAC_address = [i['mac_address'] for i in devices]


		self.database.SM.load_SensorInfo(sensor = type_d, hash_deviceid = hash_deviceid, MAC_address = MAC_address)


	def create_nonce(self):

		# This function generates the nonce. The nonce is a signature used
		# to sign requests and it is used by some Withings services.

		signature = self.api.get_signature()
		self.nonce = signature['body']['nonce']
		print('nonce', self.nonce)

	def activity_data(self): 

		# This function returns the activity data. Please refer
		# to the withings API documentation to see what type of data
		# you can get from this service.

		activity_data = {}
		scale_data = {}

		weight = []
		muscle_mass = []
		bone_mass = []
		fat_mass = []
		hydration = []

		self.meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=-8), enddateymd = arrow.utcnow().shift(days=-1))
		print('From activity service', self.meas_activity)
		activity_data['date'] = [arrow.get(x.date) for x in self.meas_activity.activities]
		activity_data['heart_rate'] = [x.hr_average for x in self.meas_activity.activities]
		activity_data['calories'] = [x.totalcalories for x in self.meas_activity.activities]
		activity_data['steps'] = [x.steps for x in self.meas_activity.activities]
		activity_data['hr_min'] = [x.hr_min for x in self.meas_activity.activities]
		activity_data['hr_max'] = [x.hr_max for x in self.meas_activity.activities]


		self.plot_continous(activity_data['date'],activity_data['calories'],activity_data['steps'],[],[], [], "ScanWatch")
		self.plot_min_max_av(activity_data['date'],activity_data['heart_rate'],activity_data['hr_min'],activity_data['hr_max'], "ScanWatch", "HR")



		self.database.SM.load_ScanWatch(hr = activity_data['heart_rate'], calories = activity_data['calories'], steps = activity_data['steps'],  time = activity_data['date'] )

		self.meas2 = self.api.measure_get_meas(startdate=arrow.utcnow().shift(days=-20), enddate=arrow.utcnow().shift(days=-1), lastupdate = None)

		scale_data['date'] = [arrow.get(x.date) for x in self.meas2.measuregrps]
		scale_data['measures'] = [x.measures for x in self.meas2.measuregrps]

		print('SCALEEEE',scale_data['measures'])




		#To extract the data from the scale
		for x in range (len(scale_data['measures'])):

			#print(scale_data['measures'][x])
			#print('-------------------------')
			for y in range (len(scale_data['measures'][x])):
				if len(scale_data['measures'][x]) == 7:

					if y == 0:
						if(scale_data['measures'][x][y].type == MeasureType.WEIGHT):
							n = self.str_to_float(number = scale_data['measures'][x][y].value, unit = scale_data['measures'][x][y].unit)
							weight.append(n)
					if y == 2:
						if(scale_data['measures'][x][y].type == MeasureType.MUSCLE_MASS):
							mm = self.str_to_float(number = scale_data['measures'][x][y].value, unit = scale_data['measures'][x][y].unit)
							muscle_mass.append(mm)

					if y == 3:
						if(scale_data['measures'][x][y].type == MeasureType.HYDRATION):
							h = self.str_to_float(number = scale_data['measures'][x][y].value, unit = scale_data['measures'][x][y].unit)
							hydration.append(h)

					if y == 4:
						if(scale_data['measures'][x][y].type == MeasureType.BONE_MASS):
							bm = self.str_to_float(number = scale_data['measures'][x][y].value, unit = scale_data['measures'][x][y].unit)
							bone_mass.append(bm)

					if y == 1:
						if(scale_data['measures'][x][y].type == MeasureType.FAT_MASS_WEIGHT):
							fm = self.str_to_float(number = scale_data['measures'][x][y].value, unit = scale_data['measures'][x][y].unit)
							fat_mass.append(fm)
				
				else:
					weight.append(0)
					muscle_mass.append(0)
					bone_mass.append(0)
					fat_mass.append(0)
					hydration.append(0)


		self.database.SM.load_Scale(time = scale_data['date'], weight = weight, muscle_mass = muscle_mass, bone_mass = bone_mass, fat_mass = fat_mass)

		self.plot_continous(scale_data['date'],weight, muscle_mass, bone_mass, fat_mass, hydration, "Scale")


	def str_to_float(self, number, unit):

		number = str(number)
		number = number[:unit] + "." + number[unit:] 
		number = float(number)

		return(number)





		

	def intra_activitydata(self):


		activity_data = {}
		watch_data = []
		HR_watch = []
		dates_hr = []
		dates = []
		HR = []
		starting_day = -8
		ending_day = -1
		week_days = list(range(starting_day, ending_day))
		print(week_days)

		total = abs(starting_day) - abs(ending_day)

		for i in range (len(week_days)):

			self.meas_intraactivity = self.api.measure_get_intraactivity(startdate=arrow.utcnow().shift(days= week_days[i]), enddate=arrow.utcnow().shift(days = week_days[i]+1),)
			
			dates = [key for key, sub_dict in self.meas_intraactivity['series'].items() if 'heart_rate' in sub_dict]
			watch_data = [sub_dict['heart_rate'] for sub_dict in self.meas_intraactivity['series'].values() if 'heart_rate' in sub_dict]

			dates_hr.append(dates)
			HR_watch.append(watch_data)



		HR_watch = sum(HR_watch,[])
		dates_hr = sum(dates_hr,[])
		dates_hr = [int(x) for x in dates_hr]




		self.meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=-8), enddateymd = arrow.utcnow().shift(days=-1))
		print('From activity service', self.meas_activity)
		activity_data['date'] = [arrow.get(x.date) for x in self.meas_activity.activities]
		activity_data['heart_rate'] = [x.hr_average for x in self.meas_activity.activities]

		self.plot_scatter(dates_hr, HR_watch, activity_data['date'], activity_data['heart_rate'], "HR_ScanWatch")
	

		



	def sleep_daily(self):

		sleephf_data = []
		sleephf_data_hr = []
		data = []
		data_hr = []
		HR_sleep = []
		starting_day = -8
		ending_day = -1

		sleeps_data = {}

		week_days = list(range(starting_day, ending_day))
		print(week_days)

		total = abs(starting_day) - abs(ending_day)

		for i in range (len(week_days)):

			self.get_sleep_1 = self.api.sleep_get(data_fields=GetSleepField,startdate=arrow.utcnow().shift(days= week_days[i]), enddate=arrow.utcnow().shift(days = week_days[i]+1),)
			sleephf_data = [x['rr'] for x in self.get_sleep_1['series']]
			sleephf_data_hr = [x['hr'] for x in self.get_sleep_1['series']]
			data.append(sleephf_data)
			data_hr.append(sleephf_data_hr)




		data = sum(data,[])
		dates = [i for s in [d.keys() for d in data] for i in s]
		dates = [int(x) for x in dates]
		RR = [i for s in [d.values() for d in data] for i in s]


		data_hr = sum(data_hr,[])
		dates_hr = [i for s in [d.keys() for d in data_hr] for i in s]
		dates_hr = [int(x) for x in dates_hr]
		HR = [i for s in [d.values() for d in data_hr] for i in s]
		#print(HR)

		self.sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days=starting_day+1),enddateymd=arrow.utcnow().shift(days=ending_day), lastupdate = None)

		#print('Sleep Summary', self.sleep_summary)

		sleeps_data['date'] = [arrow.get(x.date) for x in self.sleep_summary.series]
		sleeps_data['data'] = [x.data for x in self.sleep_summary.series]
		sleeps_data['rr average'] = [x.rr_average for x in sleeps_data['data']]
		sleeps_data['hr average'] = [x.hr_average for x in sleeps_data['data']]




		self.plot_scatter(dates, RR , sleeps_data['date'], sleeps_data['rr average'], "RR")
		self.plot_scatter(dates_hr, HR , sleeps_data['date'], sleeps_data['hr average'], "HR")
		

	def sleep(self):

		sleephf_data = {}

		sleeps_data = {}

		self.get_sleep = self.api.sleep_get(data_fields=GetSleepField,startdate=arrow.utcnow().shift(days=-11), enddate=arrow.utcnow().shift(days=-10),)
		
		#print(arrow.utcnow().shift(days=-31))
		#print(arrow.utcnow().shift(days=-30))
		#print('from sleep', self.get_sleep['series'])
		#print(self.get_sleep['series'])
		sleephf_data['start_date'] = [arrow.get(x['startdate']) for x in self.get_sleep['series']]
		sleephf_data['end_date'] = [arrow.get(x['enddate']) for x in self.get_sleep['series']]
		sleephf_data['state'] = [x['state'] for x in self.get_sleep['series']]
		sleephf_data['rr_average'] = [x['rr'] for x in self.get_sleep['series']]

		print('Respiration Rate', sleephf_data['rr_average'])


		#print(len(sleephf_data['start_date']))
		self.plot_events(sleephf_data['start_date'], sleephf_data['end_date'], sleephf_data['state'])


		


		self.sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days=-8),enddateymd=arrow.utcnow().shift(days=-1), lastupdate = None)

		print('Sleep Summary', self.sleep_summary)

		sleeps_data['date'] = [arrow.get(x.date) for x in self.sleep_summary.series]
		sleeps_data['data'] = [x.data for x in self.sleep_summary.series]

		#print(sleeps_data['data'][0])

		sleeps_data['breathing disturbances'] = [x.breathing_disturbances_intensity for x in sleeps_data['data']]
		sleeps_data['deep sleep duration'] = [x.deepsleepduration for x in sleeps_data['data']]
		sleeps_data['duration to sleep'] = [x.durationtosleep for x in sleeps_data['data']]
		sleeps_data['duration to wakeup'] = [x.durationtowakeup for x in sleeps_data['data']]
		sleeps_data['hr average'] = [x.hr_average for x in sleeps_data['data']]
		sleeps_data['hr_min'] = [x.hr_min for x in sleeps_data['data']]
		sleeps_data['hr_max'] = [x.hr_max for x in sleeps_data['data']]
		sleeps_data['light sleep duration'] = [x.lightsleepduration for x in sleeps_data['data']]
		sleeps_data['rem sleep duration'] = [x.remsleepduration for x in sleeps_data['data']]
		sleeps_data['rr average'] = [x.rr_average for x in sleeps_data['data']]
		sleeps_data['sleep score'] = [x.sleep_score for x in sleeps_data['data']]
		sleeps_data['wake up count'] = [x.wakeupcount for x in sleeps_data['data']]
		sleeps_data['total sleep time'] = [x.total_sleep_time for x in sleeps_data['data']]
		sleeps_data['total timeinbed'] = [x.total_timeinbed for x in sleeps_data['data']]
		sleeps_data['waso'] = [x.waso for x in sleeps_data['data']]
		sleeps_data['wake up duration'] = [x.wakeupduration for x in sleeps_data['data']]
		sleeps_data['awake in bed'] =  np.subtract(sleeps_data['total timeinbed'],sleeps_data['total sleep time'])
		sleeps_data['apnea'] =  [x.apnea_hypopnea_index for x in sleeps_data['data']]
		sleeps_data['out of bed count'] = [x.out_of_bed_count for x in sleeps_data['data']]


		self.database.SM.load_SleepMat(time = sleeps_data['date'], bd = sleeps_data['breathing disturbances'], dsd = sleeps_data['deep sleep duration'], dts = sleeps_data['duration to sleep'],
									dtw = sleeps_data['duration to wakeup'], hr = sleeps_data['hr average'], lsd = sleeps_data['light sleep duration'], rsd = sleeps_data['rem sleep duration'], 
									rr = sleeps_data['rr average'], ss = sleeps_data['sleep score'], wpc = sleeps_data['wake up count'], wpd = sleeps_data['wake up duration'])

		self.plot_min_max_av(sleeps_data['date'], sleeps_data['hr average'],sleeps_data['hr_min'],sleeps_data['hr_max'], "SleepMat", "HR")

		self.plot_bar(sleeps_data['date'],sleeps_data['apnea'])

		self.plot_stacked_bar(sleeps_data['date'],sleeps_data['total sleep time'],sleeps_data['awake in bed'],sleeps_data['out of bed count'], sleeps_data['wake up count'])





		



	#The following functions will be used to get the users' raw data. Please keep in mind that you need to activate and deactivate
	#the device you want to acquiere the raw data from

	def activate_raw_data(self, data_type = None):

		#This function allows the user to activate the raw data acquisition, data_type: type of data that needs to be 
		#activated (1: accelerometer, 2: optical sensor)

		self.api.activate_raw_data(hash_deviceid = self.hash_deviceid, rawdata_type = 1, enddate = arrow.utcnow().shift(days = 2))


	def deactivate_raw_data(self, data_type = None):

		#This function allows the user to deactivate the raw data acquisition, data_type: type of data that needs to be 
		#activated (1: accelerometer, 2: optical sensor)
		self.api.deactivate_raw_data(hash_deviceid = self.hash_deviceid, rawdata_type = 1)
		


	def get_raw_data(self):

		#This function allows to get the data collected during the times used in the activate_raw_data function.
		get_raw = self.api.get_raw_data(hash_deviceid = self.hash_deviceid, rawdata_type = 1, startdate = arrow.utcnow().shift(days=-20), enddate = arrow.utcnow().shift(days=-1))
		return(get_raw)



	def save_credentials(self, credentials: CredentialsType) -> None:

		"""Save credentials to a file."""
		print("Saving credentials in:", self.CREDENTIALS_FILE)
		with open(self.CREDENTIALS_FILE, "wb") as file_handle:
			pickle.dump(credentials, file_handle)


	def load_credentials(self) -> CredentialsType:

		"""Load credentials from a file."""
		print("Using credentials saved in:", self.CREDENTIALS_FILE)
		with open(self.CREDENTIALS_FILE, "rb") as file_handle:
			return cast(CredentialsType, pickle.load(file_handle))




	def plot_scatter(self, x, y, k,j, name):

		x = [datetime.fromtimestamp(timestamp) for timestamp in x]
		
		x1 = [date.strftime("%d-%b") for date in x]

		print(x1)
		data = {"Dates":x1, "Values": y}
		df = pd.DataFrame(data)


		print(k)


		plt.clf()

		# Create a scatter plot
		sns.color_palette("Set2")
		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})
		
		
		if name == 'RR':
			plt.gca().set_title('Sleep Respiration Rate', fontsize = 14, loc = 'left',pad = 30)
			plt.ylabel("Breaths per minute", fontsize = 11)
			sns.scatterplot( x= x, y = y, color = "cornflowerblue", label = 'Respiration Rate')
			sns.lineplot(x = k, y = j, color = "darkblue", marker = 'o',label = 'Respiration Rate Average')

		elif name == 'HR':
			plt.gca().set_title('Sleep Heart Rate', fontsize = 14, loc = 'left',pad = 30)
			plt.ylabel("Heart Rate (bpm)", fontsize = 11)
			sns.scatterplot( x= x, y = y, color = "cornflowerblue", label = 'Sleep Heart Rate')
			sns.lineplot(x = k, y = j, color = "darkblue", marker = 'o',label = 'Sleep Heart Rate Average')

		elif name == 'HR_ScanWatch':
			plt.gca().set_title('Daily Heart Rate', fontsize = 14, loc = 'left',pad = 30)
			plt.ylabel("Heart Rate (bpm)", fontsize = 11)
			sns.scatterplot( x= x, y = y, color = "cornflowerblue", label = 'Daily Heart Rate')
			sns.lineplot(x = k, y = j, color = "darkblue", marker = 'o',label = 'Daily Heart Rate Average')


		for x, y in zip(k, j):
			plt.text(x, y, y, ha='center', va='bottom', size = 11)

		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.grid(axis = "x")



		

		plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =2)
		
		plt.savefig('RR_SleepMat.png', dpi = 500)

		# Display the plot
		plt.show()




	def plot_min_max_av(self,x_values,y_average,y_min,y_max,device,type_d):

		x_values = [datetime.fromtimestamp(a.timestamp()) for a in x_values]

		# Calculate the range (difference between min and max)

		#print(type(y_average[1]))
		y_range = []


		y_average = [float('nan') if x == 0 else x for x in y_average]
		y_min = [float('nan') if x == 0 else x for x in y_min]
		y_max = [float('nan') if x == 0 else x for x in y_max]

		plt.clf()

		for i, j, z in zip(y_average,y_min,y_max):

			y_range.append([i-j, z-i])

		y_range = np.transpose(y_range)

		# Create the figure and axis

		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})

		# Plot the average line
		sns.scatterplot(x = x_values, y = y_average, color='green', label='Heart Rate Average')

		# Plot the error bars (range)
		plt.errorbar(x_values, y_average, yerr= y_range, fmt='o', color='green', ecolor='mediumseagreen', capsize=5)




		if device == "ScanWatch":

			
			plt.gca().set_title('ScanWatch: Heart Rate',fontsize = 14, loc = 'left',pad = 30)

		elif device == "SleepMat":
			
			plt.gca().set_title('SleepMat: Heart Rate',fontsize = 14, loc = 'left',pad = 30)

		# Add legend
		plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =2)

		# Set the x-axis format as dates
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))


		# Add average value as text
		for x, y in zip(x_values, y_average):
			plt.text(x, y, f'{y:.2f}', ha='center', va='bottom', size = 11)

		# Show the plot
		#plt.savefig('my_plot.png')
		plt.gca().yaxis.set_label_coords(-0.1,0.5)
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.grid(axis = "x")
		plt.savefig(type_d, dpi = 500)

		plt.show()




	def plot_continous(self,x,y,z,w,t,l, device):

		index_0 = [index for index, value in enumerate(y) if value == 0]

		plt.clf()


		if device == "ScanWatch":

			y = [value for value in y if value != 0]
			z = [value for value in z if value != 0]

			x = [datetime.fromtimestamp(a.timestamp()) for a in x]
			x = [value for index, value in enumerate(x) if index not in index_0]


			sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})
			sns.lineplot(x = x, y = z, color = "mediumseagreen", marker = 'o', label = "Steps" )

			# Set the x-axis format as dates
			plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
			plt.tick_params(axis = 'x', which = 'major', labelsize = 11)


			for index in range(len(x)):
				plt.text(x[index], z[index], z[index], size = 11)

			plt.gca().set_title('Daily Steps Count',fontsize = 14, loc = 'left',pad = 30)
			plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =2)
			#plt.gca().yaxis.set_label_coords(-0.1,0.5)

		elif device == "Scale":


			y = [value for value in y if value != 0]
			z = [value for value in z if value != 0]
			w = [value for value in w if value != 0]
			t = [value for value in t if value != 0]
			l = [value for value in l if value != 0]

			x = [datetime.fromtimestamp(a.timestamp()) for a in x]
			x = [value for index, value in enumerate(x) if index not in index_0]

			# Create a scatter plot
			sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})
			
			sns.lineplot(x = x, y = y, marker = 'o', label = "Weight", color = "darkblue")
			sns.lineplot(x = x, y = z, marker = 'o', label = "Muscle mass", color = "mediumseagreen" )
			sns.lineplot(x = x, y = w,  marker = 'o', label = "Bone mass", color = "slategrey" )
			sns.lineplot(x = x, y = t,  marker = 'o', label = "Fat mass", color = "mediumpurple")
			sns.lineplot(x = x, y = l,  marker = 'o', label = "Hydration", color = "cornflowerblue")

			
		


			for index in range(len(x)):
				plt.text(x[index], y[index], y[index], size = 11)
				plt.text(x[index], z[index], z[index], size = 11)
				plt.text(x[index], w[index], w[index], size = 11)
				plt.text(x[index], t[index], t[index], size = 11)
				plt.text(x[index], l[index], l[index], size = 11)

			plt.gca().set_title('Weight Trends',fontsize = 14, loc = 'left',pad = 30)
			plt.ylabel("Mass(kg)", fontsize = 11)
			plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.15), ncol = 3)



		
		# Set the x-axis format as dates
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
	
		

		# Display the plot
		
		plt.grid(axis = "x")
		plt.savefig(device, dpi = 500)
		plt.show()


	def plot_bar(self,x,y):

		# Convert Arrow datetime objects to strings

		x_labels = [a.format('MM-DD') for a in x]

		colors = ["mediumseagreen" if i < 16 else "gold" if 16 <= i < 30 else "firebrick" for i in y]

		plt.clf()

		# Create a bar plot

		plt.bar(x_labels, y, color = colors)


		# Create legend patches
		red_patch = patches.Patch(color='mediumseagreen', label='Normal/Mild(<15)')
		orange_patch = patches.Patch(color='gold', label='Moderate(16-30)')
		green_patch = patches.Patch(color='firebrick', label='Severe(>30)')



		# Label the axes and add a title


		plt.gca().set_title('Sleep Apnoea Score', fontsize = 14, loc = 'left',pad = 30)
		plt.gca().yaxis.set_label_coords(-0.1,0.5)
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		plt.grid(axis = "x")

		# Create legend slide
		plt.ylabel("Breathing disturbances per hour", fontsize = 11)
		plt.legend(handles=[red_patch, orange_patch, green_patch], loc='upper center', bbox_to_anchor=(0.5,1.09), ncol = 3)
		plt.savefig('Sleep_Apnea', dpi = 500)

		# Display the plot
		plt.show()

	def plot_stacked_bar(self,x,y,z,o,l):

		x_labels = [a.format('MM-DD') for a in x]

		y = [x/3600 for x in y]
		z = [x/3600 for x in z]
		
		plt.clf()

		plt.bar(x_labels, y, label='Hours Asleep', color = "royalblue")
		plt.bar(x_labels, z, label='Hours Awake in bed', bottom = y, color = "mediumseagreen")


		sns.lineplot(x = x_labels, y = o, color = "darkblue", marker = 'o', markersize = 14, label = "Times out of bed" )
		sns.lineplot(x = x_labels, y = l, color = "darkgreen", marker = 'o', markersize = 14, label = "Times woken up in bed" )


		for index in range(len(x)):
			plt.text(x_labels[index], o[index], o[index], size = 11, color = "white", ha = 'center', va = 'center')
			plt.text(x_labels[index], l[index], l[index], size = 11, color = "white", ha = 'center', va = 'center')

		# Add labels, title, and legend
		plt.grid(axis = "x")
		plt.ylim(bottom = -0.5)
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.ylabel('Hours', fontsize = 11)
		plt.gca().set_title('Sleep Summary', fontsize = 14, loc = 'left',pad = 30)
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =3)
		plt.savefig('sleep_summary', dpi = 500)

		# Show the chart
		plt.show()


	def plot_events(self,start_times, end_times, amplitudes):


		

		# Create a figure and axis
		fig, ax = plt.subplots()


		rect2 = []

		#print(start_times)


		# x_limit calculation
		x_lim_min = min(start_times)
		#print('Min date', x_lim_min)
		x_lim_max = max(end_times)
		#print('Min date', x_lim_max)



		
		legend_handles = {}

		# Loop through each event and plot the colored rectangle

		for start_time, end_time, amplitude in zip(start_times, end_times, amplitudes):

			# Convert start and end times to datetime objects
			start_datetime = start_time.datetime
			start_datetime = mdates.date2num(start_datetime)

			#print(start_datetime)

			end_datetime = end_time.datetime
			end_datetime = mdates.date2num(end_datetime)
			#print(end_datetime)

			# Calculate the duration of the event in minutes (as an integer)
			width = end_datetime - start_datetime

			
			# Create a rectangle patch for the event
			#print(amplitude)
			if amplitude == 1:

				color = 'blue'
				label = 'Light Sleep'

			elif amplitude == 2:
				color = 'cyan'
				label = 'Deep Sleep'
			elif amplitude == 3:
				color = 'gray'
				label = 'REM Sleep'
			else:
				color = 'white'
				label = 'Awake'



			rect = Rectangle((start_datetime, 0), width, amplitude, color = color)

			if label not in legend_handles:
				legend_handles[label] = rect

			# Add the rectangle to the plot
			ax.add_patch(rect)



		locator = mdates.AutoDateLocator(minticks = 3)
		formatter = mdates.DateFormatter(fmt = "%m-%d %H:%M" )

		ax.xaxis.set_major_locator(locator)
		ax.xaxis.set_major_formatter(formatter)

		ax.set_xlim(mdates.date2num(x_lim_min.datetime), mdates.date2num(x_lim_max.datetime))
		ax.set_ylim(0, 4)


		ax.set_ylabel('State', rotation = 0)
		ax.set_title('Sleep states', fontsize = 18)
		
		handles = list(legend_handles.values())
		labels = list(legend_handles.keys())

		# Display the plot
		plt.legend(handles= handles, labels = labels, loc = "upper right")
		plt.show()



	def pdf_generation(self):

		path = self.dir = os.getcwd()
		
		image_paths = [path +'/'+'HR.png', path +'/'+'RR_SleepMat.png', path +'/'+'Scale.png',
					   path +'/'+'ScanWatch.png', path +'/'+'Sleep_Apnea.png' ,path +'/'+'sleep_summary.png']



		c = canvas.Canvas('output.pdf', pagesize=letter)

		# Calculate the width and height of the page
		page_width, page_height = letter

		# Calculate the number of images and the matrix dimensions
		num_images = len(image_paths)
		rows = 3
		columns = 2

		# Calculate the width and height of each image within the matrix
		image_width = page_width // columns
		image_height = page_height // rows

		for i, image_path in enumerate(image_paths):

			# Calculate the row and column indices of the current image
			row = i // columns
			col = i % columns

			# Calculate the coordinates of the current image within the matrix
			x = col * image_width
			y = page_height - ((row + 1) * image_height)

			# Draw the image on the canvas
			c.drawImage(image_path, x, y, width=image_width, height=image_height)


		# Save the canvas as a PDF file
		c.save()



		





M = Devices_OAuth2flow(client_id = 'e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc', 
		       costumer_secret = 'c2b3bd8f8fa210533aa3e7ef54abd4654d2a44cfe4f33d9f3aff63b4ce0943c4',
		       callback_uri = 'http://localhost:5000')
M.get_user_credentials()
M.devices_info()
M.intra_activitydata()
M.activity_data()
M.sleep_daily()
M.sleep()
#M.pdf_generation()
#M.deactivate_raw_data()
#M.activate_raw_data()
