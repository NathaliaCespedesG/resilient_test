import sys
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from withings_api import WithingsAuth, WithingsApi, AuthScope
from withings_api.common import GetSleepField, GetSleepSummaryField, get_measure_value, MeasureType, CredentialsType, MeasureGetActivityResponse, AuthFailedException
import arrow
import time
import numpy as np
import math



#To save users credential and update refresh the token

import argparse
import os
from os import path
import pickle
from typing import cast
from urllib import parse
from typing_extensions import Final
import pandas as pd 


# Database libraries to save Users' data 
import db.database as database
# Database libraries to save Users' data 
import resources.PDF_generation as pdf_gen


# Graphics

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import timedelta, datetime
from matplotlib.path import Path
import seaborn as sns
import itertools
import matplotlib.patches as patches
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from scipy.interpolate import make_interp_spline

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

		#Create an ID for each user

		id_user = input('Please provide the id for the user: ')

		self.database.register(user = id_user)


		#Create the credentials File
		# This file has the authorization and refresh token which are
		# used to acquire the data fromo Withings server 

		self.base_path = path.dirname(os.path.abspath(__file__))
		additional_path = "db/General"
		credentials_path = ".credentials"

		self.final_path = path.abspath(path.join(self.base_path, additional_path, id_user, credentials_path))

		time.sleep(1)

		self.CREDENTIALS_FILE: Final = self.final_path
		self.dates()




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




	def dates(self):

		self.starting_day_p = -46
		self.ending_day_p = -40
		self.starting_day_c = -39
		self.ending_day_c = -32

		# Dates
		self.initial_dates = arrow.utcnow().shift(days = self.starting_day_c)
		self.initial_dates_table = self.initial_dates.format('D MMMM ')


		self.ending_dates = arrow.utcnow().shift(days = self.ending_day_c)
		self.ending_dates_table = self.ending_dates.format('D MMMM ')


	


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
		pre_activity_data = {}
		scale_data = {}
		scale_data_c = {}
		scale_data_p = {}

		

		self.meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=self.starting_day_c), enddateymd = arrow.utcnow().shift(days= self.ending_day_c))
		self.prev_meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=self.starting_day_p), enddateymd = arrow.utcnow().shift(days= self.ending_day_p))
		 
		print(self.meas_activity)
		
		#Current Week
		activity_data['date'] = [arrow.get(x.date) for x in self.meas_activity.activities]
		activity_data['heart_rate'] = [x.hr_average for x in self.meas_activity.activities]
		activity_data['calories'] = [x.totalcalories for x in self.meas_activity.activities]
		activity_data['steps'] = [x.steps for x in self.meas_activity.activities]
		activity_data['hr_min'] = [x.hr_min for x in self.meas_activity.activities]
		activity_data['hr_max'] = [x.hr_max for x in self.meas_activity.activities]
		#Previous Week
		pre_activity_data['heart_rate'] = [x.hr_average for x in self.prev_meas_activity.activities]
		pre_activity_data['steps'] = [x.steps for x in self.prev_meas_activity.activities]

		self.HR_table = ([activity_data['heart_rate'], pre_activity_data['heart_rate']]) 
		self.Steps_table = ([activity_data['steps'], pre_activity_data['steps']])


		self.plot_curved_bars(activity_data['date'],activity_data['steps'])


		self.database.SM.load_ScanWatch(hr = activity_data['heart_rate'], calories = activity_data['calories'], steps = activity_data['steps'],  time = activity_data['date'] )

		scale_starting_date = arrow.utcnow().shift(days= self.ending_day_c - 30)
		scale_ending_date = arrow.utcnow().shift(days = self.ending_day_c)

		self.meas2 = self.api.measure_get_meas(startdate = scale_starting_date, enddate = scale_ending_date, lastupdate = None)
		self.meas_current = self.api.measure_get_meas(startdate=arrow.utcnow().shift(days= self.starting_day_c), enddate=arrow.utcnow().shift(days= self.ending_day_c), lastupdate = None)
		self.meas_prev = self.api.measure_get_meas(startdate=arrow.utcnow().shift(days= self.starting_day_p), enddate=arrow.utcnow().shift(days= self.ending_day_p), lastupdate = None)



		scale_data['date'] = [arrow.get(x.date) for x in self.meas2.measuregrps]
		scale_data['measures'] = [x.measures for x in self.meas2.measuregrps]

		#Current week average
		scale_data_c['measures'] = [x.measures for x in self.meas_current.measuregrps]		
		#Previous week average
		scale_data_p['measures'] = [x.measures for x in self.meas_prev.measuregrps]
		


		#To extract the data from the scale (Monthly)
		weight, muscle_mass, bone_mass, fat_mass, hydration = self.scale_data_extractor(scale_data['measures'])

		#Scale data (current week)

		weight_c, muscle_mass_c, bone_mass_c, fat_mass_c, hydration_c = self.scale_data_extractor(scale_data_c['measures'])

		weight_p, muscle_mass_p, bone_mass_p, fat_mass_p, hydration_p = self.scale_data_extractor(scale_data_p['measures'])

		self.Weight_table = (weight_c, weight_p)

		self.database.SM.load_Scale(time = scale_data['date'], weight = weight, muscle_mass = muscle_mass, bone_mass = bone_mass, fat_mass = fat_mass)

		self.plot_continous(scale_data['date'],weight, muscle_mass, bone_mass, fat_mass, hydration, scale_starting_date, scale_ending_date, "Scale")
		
	def scale_data_extractor(self, data):

		weight = []
		muscle_mass = []
		bone_mass = []
		fat_mass = []
		hydration = []

		#To extract the data from the scale
		for x in range (len(data)):

			#print(scale_data['measures'][x])
			#print('-------------------------')
			for y in range (len(data[x])):
				if len(data[x]) == 7:

					if y == 0:
						if(data[x][y].type == MeasureType.WEIGHT):
							n = self.str_to_float(number = data[x][y].value, unit = data[x][y].unit)
							weight.append(n)
					if y == 2:
						if(data[x][y].type == MeasureType.MUSCLE_MASS):
							mm = self.str_to_float(number = data[x][y].value, unit = data[x][y].unit)
							muscle_mass.append(mm)

					if y == 3:
						if(data[x][y].type == MeasureType.HYDRATION):
							h = self.str_to_float(number = data[x][y].value, unit = data[x][y].unit)
							hydration.append(h)

					if y == 4:
						if(data[x][y].type == MeasureType.BONE_MASS):
							bm = self.str_to_float(number = data[x][y].value, unit = data[x][y].unit)
							bone_mass.append(bm)

					if y == 1:
						if(data[x][y].type == MeasureType.FAT_MASS_WEIGHT):
							fm = self.str_to_float(number = data[x][y].value, unit = data[x][y].unit)
							fat_mass.append(fm)
				
				else:
					weight.append(0)
					muscle_mass.append(0)
					bone_mass.append(0)
					fat_mass.append(0)
					hydration.append(0)


		return(weight, muscle_mass, bone_mass, fat_mass, hydration)




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
		starting_day = self.starting_day_c
		ending_day = self.ending_day_c
		week_days = list(range(starting_day, ending_day))
		#print(week_days)

		total = abs(starting_day) - abs(ending_day)

		for i in range (len(week_days)):

			self.meas_intraactivity = self.api.measure_get_intraactivity(startdate=arrow.utcnow().shift(days= week_days[i]), enddate=arrow.utcnow().shift(days = week_days[i]+1),)
			
			dates = [key for key, sub_dict in self.meas_intraactivity['series'].items() if 'heart_rate' in sub_dict]
			watch_data = [sub_dict['heart_rate'] for sub_dict in self.meas_intraactivity['series'].values() if 'heart_rate' in sub_dict]
			print(watch_data)

			print(np.mean(watch_data))
			dates_hr.append(dates)
			HR_watch.append(watch_data)



		HR_watch = sum(HR_watch,[])
		dates_hr = sum(dates_hr,[])
		dates_hr = [int(x) for x in dates_hr]




		self.meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days= self.starting_day_c), enddateymd = arrow.utcnow().shift(days= self.ending_day_c))
		#print('From activity service', self.meas_activity)
		activity_data['date'] = [arrow.get(x.date) for x in self.meas_activity.activities]
		activity_data['heart_rate'] = [x.hr_average for x in self.meas_activity.activities]

		self.plot_scatter(dates_hr, HR_watch, activity_data['date'], activity_data['heart_rate'], "HR_ScanWatch")
	

		



	def sleep_daily(self):

		sleephf_data = []
		sleephf_data_hr = []
		data = []
		data_hr = []
		HR_sleep = []
		starting_day = self.starting_day_c
		ending_day = self.ending_day_c

		sleeps_data = {}

		week_days = list(range(starting_day, ending_day))
		total = abs(starting_day) - abs(ending_day)

		for i in range (len(week_days)):

			self.get_sleep_1 = self.api.sleep_get(data_fields=GetSleepField,startdate=arrow.utcnow().shift(days= week_days[i]), enddate=arrow.utcnow().shift(days = week_days[i]+1),)
			#print(self.get_sleep_1)
			try:
				sleephf_data = [x['rr'] for x in self.get_sleep_1['series']]
				sleephf_data_hr = [x['hr'] for x in self.get_sleep_1['series']]
				data.append(sleephf_data)
				data_hr.append(sleephf_data_hr)
			except:
				print("Missing sleep data")




		data = sum(data,[])
		dates = [i for s in [d.keys() for d in data] for i in s]
		dates = [int(x) for x in dates]
		RR = [i for s in [d.values() for d in data] for i in s]


		data_hr = sum(data_hr,[])
		dates_hr = [i for s in [d.keys() for d in data_hr] for i in s]
		dates_hr = [int(x) for x in dates_hr]
		HR = [i for s in [d.values() for d in data_hr] for i in s]
		#print(HR)

		self.sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days=self.starting_day_c),enddateymd=arrow.utcnow().shift(days=self.ending_day_c), lastupdate = None)

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

		prev_sleeps_data = {}

		self.get_sleep = self.api.sleep_get(data_fields=GetSleepField,startdate=arrow.utcnow().shift(days= self.starting_day_c), enddate=arrow.utcnow().shift(days= self.ending_day_c),)
		
		sleephf_data['start_date'] = [arrow.get(x['startdate']) for x in self.get_sleep['series']]
		sleephf_data['end_date'] = [arrow.get(x['enddate']) for x in self.get_sleep['series']]
		sleephf_data['state'] = [x['state'] for x in self.get_sleep['series']]


		self.sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days = self.starting_day_c),enddateymd=arrow.utcnow().shift(days = self.ending_day_c), lastupdate = None)
		self.prev_sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days = self.starting_day_p),enddateymd=arrow.utcnow().shift(days= self.ending_day_p), lastupdate = None)

		sleeps_data['date'] = [arrow.get(x.date) for x in self.sleep_summary.series]
		sleeps_data['data'] = [x.data for x in self.sleep_summary.series]

		prev_sleeps_data['date'] = [arrow.get(x.date) for x in self.prev_sleep_summary.series]
		prev_sleeps_data['data'] = [x.data for x in self.prev_sleep_summary.series]

		sleeps_data['breathing disturbances'] = [x.breathing_disturbances_intensity for x in sleeps_data['data']]
		sleeps_data['deep sleep duration'] = [x.deepsleepduration for x in sleeps_data['data']]
		sleeps_data['duration to sleep'] = [x.durationtosleep for x in sleeps_data['data']]
		sleeps_data['duration to wakeup'] = [x.durationtowakeup for x in sleeps_data['data']]
		sleeps_data['hr average'] = [x.hr_average for x in sleeps_data['data']]
		sleeps_data['hr_min'] = [x.hr_min for x in sleeps_data['data']]
		sleeps_data['hr_max'] = [x.hr_max for x in sleeps_data['data']]
		sleeps_data['rr_min'] = [x.rr_min for x in sleeps_data['data']]
		sleeps_data['rr_max'] = [x.rr_max for x in sleeps_data['data']]
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

		# Previous week values

		prev_sleeps_data['hr average'] = [x.hr_average for x in prev_sleeps_data['data']]
		prev_sleeps_data['rr average'] = [x.rr_average for x in prev_sleeps_data['data']]
		prev_sleeps_data['total sleep time'] = [x.total_sleep_time for x in prev_sleeps_data['data']]
		prev_sleeps_data['apnea'] = [x.apnea_hypopnea_index for x in prev_sleeps_data['data']]

		self.HR_Sleep_table = ([sleeps_data['hr average'], prev_sleeps_data['hr average']])
		self.RR_Sleep_table = ([sleeps_data['rr average'], prev_sleeps_data['rr average']])
		sleeps_data['total sleep time']=[x/3600 for x in sleeps_data['total sleep time']]
		sleeps_data['awake in bed']=[x/3600 for x in sleeps_data['awake in bed']]
		prev_sleeps_data['total sleep time']=[x/3600 for x in prev_sleeps_data['total sleep time']]

		print(sleeps_data['total sleep time'])
		print(prev_sleeps_data['total sleep time'])
		self.ST_Sleep_table = ([sleeps_data['total sleep time'], prev_sleeps_data['total sleep time']])
		self.AP_Sleep_table = ([sleeps_data['apnea'], prev_sleeps_data['apnea']])




		self.database.SM.load_SleepMat(time = sleeps_data['date'], bd = sleeps_data['breathing disturbances'], dsd = sleeps_data['deep sleep duration'], dts = sleeps_data['duration to sleep'],
									dtw = sleeps_data['duration to wakeup'], hr = sleeps_data['hr average'], lsd = sleeps_data['light sleep duration'], rsd = sleeps_data['rem sleep duration'], 
									rr = sleeps_data['rr average'], ss = sleeps_data['sleep score'], wpc = sleeps_data['wake up count'], wpd = sleeps_data['wake up duration'])

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



	def unique_values(self, dates, values):

		# Convert date strings to NumPy datetime64
		x = np.array(dates, dtype='datetime64')
		# Convert values to NumPy array
		y = np.array(values)

		# Get unique dates
		unique_dates = np.unique(x)

		# Calculate average value for each unique date
		averaged_values = []
		for date in unique_dates:
			mask = x == date
			avg_value = np.mean(y[mask])
			averaged_values.append(avg_value)


		# Convert back to NumPy arrays
		x_unique = np.array(unique_dates, dtype='datetime64')
		y_avg = np.array(averaged_values)

		return(x_unique, y_avg)


	def smooth_lines(self,x,y):

		# Convert datetime objects to matplotlib date numbers
		x = mdates.date2num(x)
		y = y

		

		# Interpolate y values using the new x values

		try:
			# Create interpolation function
			interpolation_function = make_interp_spline(x, y)

			# Generate new x values for smooth curve

			new_x = np.linspace(min(x), max(x), num=50)
			smooth_y = interpolation_function(new_x)
			# Convert matplotlib date numbers back to datetime objects
			smooth_dates = mdates.num2date(new_x)

			return(smooth_dates,smooth_y)

		except:
			return(x,y)



	def plot_scatter(self, x, y, k,j, name):

		fig, ax = plt.subplots()

		

		index_0 = [index for index, value in enumerate(y) if value is None or value == 0]
		index_1 = [index for index, value in enumerate(j) if value is None or value == 0]


		y = [value for value in y if value is not None and value != 0]
		j = [value for value in j if value is not None and value != 0]

		x = [datetime.fromtimestamp(timestamp) for timestamp in x]
		x = [value for index, value in enumerate(x) if index not in index_0]
		k = [value for index, value in enumerate(k) if index not in index_1]
		k = [arrow_datetime.datetime for arrow_datetime in k]

		#Avoid double values
		k,j = self.unique_values(k,j)
		# Smooth lines
		k_s,j_s = self.smooth_lines(k,j)


		


		plt.clf()

		# Create a scatter plot
		sns.color_palette("Set2")
		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})
		
		
		if name == 'RR':
			plt.gca().set_title('Sleep Respiration Rate', fontsize = 14, loc = 'left',pad = 30, fontweight= 600)
			plt.ylabel("Breaths per minute", fontsize = 11)
			sns.scatterplot( x= x, y = y, color = "cornflowerblue", label = 'Respiration Rate')
			sns.lineplot(x = k_s, y = j_s, color = "darkblue",label = 'Respiration Rate Average')

			fig_size = fig.get_size_inches()
			print('FIG SIZE', fig_size)

			for t, t1 in zip(k, j):
				if math.isnan(t1):
					plt.text(t, t1-(0.1* fig_size[1]), math.floor(t1), ha='center', va='center', size = 11.2, color = "black")
				else:
					circle = patches.Ellipse((t, t1), width= 0.045 * fig_size[0], height= 0.3* fig_size[1], facecolor= "white")
					circle.set_zorder(5)
					plt.gca().add_patch(circle)
					plt.text(t, t1-(0.1* fig_size[1]), math.floor(t1), ha='center', va='bottom', size = 11.5, color ="black", zorder=6)

		elif name == 'HR':
		
			plt.gca().set_title('Sleep Heart Rate', fontsize = 14, loc = 'left',pad = 30, fontweight= 600)
			plt.ylabel("Heart Rate (bpm)", fontsize = 11)
			sns.scatterplot( x= x, y = y, color = "cornflowerblue", label = 'Sleep Heart Rate')
			sns.lineplot(x = k_s, y = j_s, color = "darkblue",label = 'Sleep Heart Rate Average')

			fig_size = fig.get_size_inches()
			print('FIG SIZE', fig_size)

			for t, t1 in zip(k, j):
				if math.isnan(t1):
					plt.text(t, t1-(0.32* fig_size[1]), math.floor(t1), ha='center', va='center', size = 11.2, color = "black")
				else:
					circle = patches.Ellipse((t, t1), width= 0.06 * fig_size[0], height= 0.6* fig_size[1], facecolor= "white")
					circle.set_zorder(5)
					plt.gca().add_patch(circle)
					plt.text(t, t1-(0.32* fig_size[1]), math.floor(t1), ha='center', va='bottom', size = 11.2, color ="black",zorder=6)

		elif name == 'HR_ScanWatch':
			

			plt.gca().set_title('Daily Heart Rate', fontsize = 14, loc = 'left',pad = 30, fontweight= 600)
			plt.ylabel("Heart Rate (bpm)", fontsize = 11)
			sns.scatterplot( x= x, y = y, color = "cornflowerblue", label = 'Daily Heart Rate')
			sns.lineplot(x = k_s, y = j_s, color = "darkblue",label = 'Daily Heart Rate Average')

			fig_size = fig.get_size_inches()
			print('FIG SIZE', fig_size)

			for t, t1 in zip(k, j):
				if math.isnan(t1):
					plt.text(t, t1, t1, ha='center', va='center', size = 11.2, color = "black")
				else:
					circle = patches.Ellipse((t, t1), width= 0.05 * fig_size[0], height= 1.5* fig_size[1], facecolor= "white")
					circle.set_zorder(5)
					plt.gca().add_patch(circle)
					plt.text(t, t1-(0.75* fig_size[1]), math.floor(t1), ha='center', va='bottom', size = 11.2, color ="black", zorder=6)


		try:
			plt.ylim(min(y), max(y))
		except:
			print('Empty data')
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		# Set the locator for x-axis labels
		plt.gca().xaxis.set_major_locator(mdates.DayLocator())
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.grid(axis = "x")

		plt.gca().spines['top'].set_visible(False)
		plt.gca().spines['right'].set_visible(False)



		

		plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =2 , frameon=False)
		# Remove the border around the legend box
		
		
		plt.savefig(name + 'Scatter.png', dpi = 500)

		# Display the plot
		#plt.show()




	def plot_min_max_av(self,x_values,y_average,y_min,y_max,device,type_d):

		x_values = [datetime.fromtimestamp(a.timestamp()) for a in x_values]

		# Calculate the range (difference between min and max)

		y_range = []

		y_average = [float('nan') if element is None else element for element in y_average]
		y_min = [float('nan') if element is None else element for element in y_min]
		y_max = [float('nan') if element is None else element for element in y_max]

		y_average = [float('nan') if x == 0 else x for x in y_average]
		y_min = [float('nan') if x == 0 else x for x in y_min]
		y_max = [float('nan') if x == 0 else x for x in y_max]

		print('x_values', x_values)
		print('y_values', y_average)


		x_values1, y_average = self.unique_values(x_values, y_average)
		x_values1, y_min = self.unique_values(x_values, y_min)
		x_values1, y_max = self.unique_values(x_values, y_max)


		plt.clf()

		for i, j, z in zip(y_average,y_min,y_max):

			y_range.append([i-j, z-i])

		y_range = np.transpose(y_range)

		# Create the figure and axis

		sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})

		# Plot the average line
		sns.scatterplot(x = x_values1, y = y_average, color='green', label='Heart Rate Average')

		# Plot the error bars (range)
		plt.errorbar(x_values1, y_average, yerr= y_range, fmt='o', color='green', ecolor='mediumseagreen', capsize=5)




		if device == "ScanWatch":

			
			plt.gca().set_title('ScanWatch: Heart Rate',fontsize = 14, loc = 'left',pad = 30, fontweight = 600)

		elif device == "SleepMat" and type_d == "HR":
			
			plt.gca().set_title('SleepMat: Heart Rate',fontsize = 14, loc = 'left',pad = 30, fontweight = 600)

		elif device == "SleepMat" and type_d == "RR":
			
			plt.gca().set_title('SleepMat: Respiration Rate',fontsize = 14, loc = 'left',pad = 30, fontweight = 600)

		# Add legend
		plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =2)
		# Remove the border around the legend box
		plt.legend().set_frame_on(False)

		# Set the x-axis format as dates
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		# Set the locator for x-axis labels
		plt.gca().xaxis.set_major_locator(mdates.DayLocator())


		# Add average value as text
		for x, y in zip(x_values1, y_average):
			if math.isnan(y):
				plt.text(x, y, y, ha='center', va='bottom', size = 11.5)
			else:
				plt.text(x, y, math.floor(y), ha='center', va='bottom', size = 11.5)


		# Show the plot
		#plt.savefig('my_plot.png')
		plt.gca().yaxis.set_label_coords(-0.1,0.5)
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.grid(axis = "x")
		# Remove the top and right spines
		plt.gca().spines['top'].set_visible(False)
		plt.gca().spines['right'].set_visible(False)
		plt.savefig(device+"_"+type_d, dpi = 500)

		#plt.show()




	def plot_continous(self,x,y,z,w,t,l,st_date, ed_date, device):

		st_date = st_date.format("D - MMM")
		ed_date = ed_date.format("D - MMM")

		index_0 = [index for index, value in enumerate(z) if value is None or value == 0 or math.isnan(value)]

		plt.clf()


		t = [value for value in t if value is not None and value != 0 and not math.isnan(value)]
		l = [value for value in l if value is not None and value != 0 and not math.isnan(value)]

		x = [datetime.fromtimestamp(a.timestamp()) for a in x]
		print(x)
		y = [value for value in y if value is not None and value != 0 and not math.isnan(value)]
		z = [value for value in z if value is not None and value != 0 and not math.isnan(value)]
		w = [value for value in w if value is not None and value != 0 and not math.isnan(value)]
		x = [value for index, value in enumerate(x) if index not in index_0]

		print('Scale', x)
		print(y)


		#Avoid double values
		x1,y1 = self.unique_values(x,y)
		x1,z1 = self.unique_values(x,z)
		x1,w1 = self.unique_values(x,w)
		x1,t1 = self.unique_values(x,t)
		x1,l1 = self.unique_values(x,l)

		print('ACA', x1)
		print(y1)

		# Smooth lines
		x_s,y_s = self.smooth_lines(x1,y1)
		x_s,z_s = self.smooth_lines(x1,z1)
		x_s,w_s = self.smooth_lines(x1,w1)
		x_s,t_s = self.smooth_lines(x1,t1)
		x_s,l_s = self.smooth_lines(x1,l1)

		plt.gca().set_xticks(x)

		if device == "Scale":

			# Create a scatter plot
			sns.set_style("whitegrid",{ "grid.linewidth":0.5, "grid.color": ".8", "grid.linestyle": ":", "ytick.left": True})
			
			sns.lineplot(x = x_s, y = y_s, label = "Weight", color = "darkblue", linewidth = 2)
			sns.lineplot(x = x_s, y = z_s, label = "Muscle mass", linestyle='--',  color = "mediumseagreen", linewidth = 2)
			sns.lineplot(x = x_s, y = w_s, label = "Bone mass",linestyle='--',  color = "yellow", linewidth = 2)
			sns.lineplot(x = x_s, y = t_s, label = "Fat mass", linestyle='--', color = "mediumpurple", linewidth = 2)
			sns.lineplot(x = x_s, y = l_s, label = "Hydration (%)", linestyle='--', color = "cornflowerblue", linewidth = 2)
			# Set x-axis tick locations and labels

			# Make specific ticks transparent or not display them
			plt.gca().set_xticks([])

			for index in range(len(x)):
				plt.text(x[index], y[index], math.floor(y[index]), size = 11.5,  rotation = 45)
				plt.text(x[index], z[index], math.floor(z[index]), size = 11.5,  rotation = 45)
				plt.text(x[index], w[index], math.floor(w[index]), size = 11.5,  rotation = 45)
				plt.text(x[index], t[index], math.floor(t[index]), size = 11.5,  rotation = 45)
				plt.text(x[index], l[index], math.floor(l[index]), size = 11.5,  rotation = 45)

			plt.ylim(min(w_s) - 5, max(y_s)+15)
			#plt.xlabel("From" + x[0] + "to" + x[end]))

			plt.gca().set_title('Weight Trends',fontsize = 14, loc = 'left',pad = 30, fontweight= 600)
			plt.ylabel("Mass (kg)")
			plt.xlabel(st_date +" to "+ ed_date)
			plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol = 4, fontsize = 8.5,frameon=False)

			# Set the x-axis format as dates

			#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		
			plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
			plt.gca().spines['top'].set_visible(False)
			plt.gca().spines['right'].set_visible(False)

			# Display the plot
		
			plt.grid(axis = "x")
		


		elif device == "Scale_sub":


			fig, axes = plt.subplots(nrows=5, ncols=1, figsize=(8, 12))  # Adjust figsize as needed
			# For example, plot data on the first subplot (axes[0])
			axes[0].plot(x_s, y_s, label = "Weight", color = "darkblue", linewidth = 2)
			axes[1].plot(x_s, z_s, label = "Muscle mass", linestyle='--',  color = "mediumseagreen", linewidth = 2)
			axes[2].plot(x_s, w_s, label = "Bone mass",linestyle='--',  color = "yellow", linewidth = 2)
			axes[3].plot(x_s, t_s, label = "Fat mass", linestyle='--', color = "mediumpurple", linewidth = 2)
			axes[4].plot(x_s, l_s, label = "Hydration", linestyle='--', color = "cornflowerblue", linewidth = 2)

			# Adjust spacing between subplots
			plt.tight_layout()

			for index in range(len(x)):
				axes[0].text(x[index], y[index], math.floor(y[index]), size = 11.5,  rotation = 45)
				axes[1].text(x[index], z[index], math.floor(z[index]), size = 11.5,  rotation = 45)
				axes[2].text(x[index], w[index], math.floor(w[index]), size = 11.5,  rotation = 45)
				axes[3].text(x[index], t[index], math.floor(t[index]), size = 11.5,  rotation = 45)
				axes[4].text(x[index], l[index], math.floor(l[index]), size = 11.5,  rotation = 45)


		plt.savefig(device, dpi = 500)
		#plt.show()



		


	def plot_curved_bars(self,x,y):

		#x = [datetime.fromtimestamp(a.timestamp()) for a in x]

		# Create a figure and axes

		check = np.array(y)

		if y == [] or (np.all(check == 0)):

			fig, ax = plt.subplots()

			# Step 3 (Optional): Add labels and titles to the plot
			ax.set_xlabel('X-axis label')
			ax.set_ylabel('Y-axis label')
			ax.set_title('Empty Plot')


		else:

			fig, ax = plt.subplots()

			x = [a.format('DD-MM') for a in x]

			converted_dates = []

			for date in x:
				dt = datetime.strptime(date, '%d-%m')
				converted_date = dt.strftime('%d-%b')
				converted_dates.append(converted_date)

			print(converted_dates)
			# Calculate the width of each rectangle
			width = 0.2

			legend_handles = {}
			# Create rounded rectangles for each date
			for i, date in enumerate(x):

				label = "Steps"

				rect = mpatches.FancyBboxPatch((i - width / 2, 0), width, y[i], mutation_scale=0.2, edgecolor= None,
                                  facecolor='lightgreen')

				rect.set_boxstyle("round", pad=0.3, rounding_size=0.4)
				ax.add_patch(rect)

				if label not in legend_handles:
					legend_handles[label] = rect


			# Set x-axis labels

			ax.set_xticks(range(len(converted_dates)))
			ax.set_xticklabels(converted_dates)


	

			ax.set_ylim(0, max(y) * 1.1)

			plt.grid(axis = "x")

			handles = list(legend_handles.values())
			labels = list(legend_handles.keys())

			# Display the plot
			plt.legend(handles= handles, labels = labels, loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =1, frameon=False)
			plt.gca().set_title('Daily Steps Count',fontsize = 14, loc = 'left',pad = 30, fontweight= 600)
			plt.gca().spines['top'].set_visible(False)
			plt.gca().spines['right'].set_visible(False)
		
			plt.savefig('Steps_curvedbar', dpi = 500)



		# Display the plot
		#plt.show()



	def plot_bar(self,x,y):

		# Convert Arrow datetime objects to strings

		#x_labels = [a.format('MM-DD') for a in x]
		x = [datetime.fromtimestamp(a.timestamp()) for a in x]

		y = [ 0 if element is None else element for element in y]

		x, y = self.unique_values(x,y) 

		colors = ["mediumseagreen" if i < 16 else "gold" if 16 <= i < 30 else "firebrick" for i in y]

		plt.clf()

		# Create a bar plot

		plt.bar(x, y, color = colors)


		# Create legend patches
		red_patch = patches.Patch(color='mediumseagreen', label='Normal/Mild(<15)')
		orange_patch = patches.Patch(color='gold', label='Moderate(16-30)')
		green_patch = patches.Patch(color='firebrick', label='Severe(>30)')



		# Label the axes and add a title


		plt.gca().set_title('Sleep Apnoea Score', fontsize = 14, loc = 'left',pad = 30, fontweight= 600)
		plt.gca().yaxis.set_label_coords(-0.1,0.5)
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		# Set the locator for x-axis labels
		plt.gca().xaxis.set_major_locator(mdates.DayLocator())

		plt.grid(axis = "x")

		# Create legend slide
		plt.ylabel("Breathing disturbances per hour", fontsize = 11)
		plt.legend(handles=[red_patch, orange_patch, green_patch], loc='upper center', bbox_to_anchor=(0.5,1.09), ncol = 3, frameon=False)
		plt.savefig('Sleep_Apnea', dpi = 500)

		# Display the plot
		#plt.show()

	def plot_stacked_bar(self,x,y,z,o,l):

		x = [datetime.fromtimestamp(a.timestamp()) for a in x]

		#print('x from this', x)

		#y = [x/3600 for x in y]
		#z = [x/3600 for x in z]

		x1, y = self.unique_values(x,y)
		x1, z = self.unique_values(x,z)

		x_u, o_u = self.unique_values(x,o)
		x_u, l_u = self.unique_values(x,l)


		x_soft, o_soft= self.smooth_lines(x_u,o_u)
		x_soft, l_soft = self.smooth_lines(x_u,l_u)

		plt.clf()

		plt.bar(x1, y, label='Hours Asleep', color = "cornflowerblue")
		plt.bar(x1, z, label='Hours Awake in bed', bottom = y, color = "lightgreen")


		sns.lineplot(x = x_soft, y = o_soft, color = "darkblue", markersize = 14, label = "Times out of bed", zorder = 9, linewidth = 2 )
		sns.lineplot(x = x_soft, y = l_soft, color = "darkgreen", markersize = 14, label = "Times woken up in bed" , zorder = 9, linewidth = 2)


		for index in range(len(x_u)):
			# Draw the circle patch
			circle = patches.Ellipse((x_u[index], o_u[index]), width= 0.35, height= 0.65, facecolor= "lavender")
			plt.gca().add_patch(circle)
			circle1 = patches.Ellipse((x_u[index], l_u[index]), width= 0.35, height= 0.65, facecolor= "honeydew")
			circle.set_zorder(10)
			circle1.set_zorder(10)
			plt.gca().add_patch(circle1)
			plt.text(x_u[index], o_u[index], math.floor(o_u[index]), size = 11.5, color = "black", ha = 'center', va = 'center', zorder = 11 )
			plt.text(x_u[index], l_u[index], math.floor(l_u[index]), size = 11.5, color = "black", ha = 'center', va = 'center', zorder = 11 )

		# Add labels, title, and legend
		print(max(y+z))
		plt.grid(axis = "x")
		plt.ylim(bottom = -1)
		plt.ylim(top= (max(y+z)+1))
		plt.tick_params(axis = 'x', which = 'major', labelsize = 11)
		plt.ylabel('Hours', fontsize = 11)
		plt.gca().set_title('Sleep Summary', fontsize = 14, loc = 'left',pad = 30, fontweight=600)
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
		# Set the locator for x-axis labels
		plt.gca().spines['top'].set_visible(False)
		plt.gca().spines['right'].set_visible(False)
		#plt.gca().xaxis.set_major_locator(mdates.DayLocator())
		plt.legend(loc= 'upper center', bbox_to_anchor = (0.5,1.09), ncol =3, fontsize = 8.5, frameon=False)
		plt.savefig('sleep_summary', dpi = 500)

		# Show the chart
		#plt.show()


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

		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)

		# Display the plot
		plt.legend(handles= handles, labels = labels, loc = "upper right", frameon=False)
		#plt.show()



	def doc_generation(self):

		path = self.database.SM.get_path()

		print('PATAHAHAH', path)

		self.document_generation = pdf_gen.PDF_generation(day_hr = self.HR_table, 
					night_hr = self.HR_Sleep_table, 
					night_rr = self.RR_Sleep_table,
					steps = self.Steps_table, 
					sleep_duration = self.ST_Sleep_table, 
					sleep_apnoea = self.AP_Sleep_table,
					weight = self.Weight_table,
					c_date = self.initial_dates_table,
					e_date = self.ending_dates_table,
					path = path)


	def remove_images(self):

		files_in_folder = os.listdir(self.base_path)

		for file_name in files_in_folder:
			file_path = os.path.join(self.base_path, file_name)
			if os.path.isfile(file_path) and file_name.lower().endswith('.png'):
				os.remove(file_path)
				print(f"Removed: {file_name}")
			else:
				print(f"Skipped: {file_name}")






M = Devices_OAuth2flow(client_id = 'e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc', 
		       costumer_secret = 'c2b3bd8f8fa210533aa3e7ef54abd4654d2a44cfe4f33d9f3aff63b4ce0943c4',
		       callback_uri = 'http://localhost:5000')
M.get_user_credentials()
M.devices_info()
M.intra_activitydata()
M.activity_data()
M.sleep_daily()
M.sleep()
#M.table()
M.doc_generation()
M.remove_images()
#M.deactivate_raw_data()
#M.activate_raw_data()
