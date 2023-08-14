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


# Module: Database libraries to save Users' data 
import db.database as database
#Module: Graphics generation class
import resources.Graph_generation as graph
# Module: PDF generation class to generate the reports 
import resources.PDF_generation as pdf_gen


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

		self.graph = graph.Graph_generator()


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


		self.graph.plot_curved_bars(activity_data['date'],activity_data['steps'])


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

		self.graph.plot_continous(scale_data['date'],weight, muscle_mass, bone_mass, fat_mass, hydration, scale_starting_date, scale_ending_date, "Scale")
		
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

		self.graph.plot_scatter(dates_hr, HR_watch, activity_data['date'], activity_data['heart_rate'], "HR_ScanWatch")
	

		



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


		self.graph.plot_scatter(dates, RR , sleeps_data['date'], sleeps_data['rr average'], "RR")
		self.graph.plot_scatter(dates_hr, HR , sleeps_data['date'], sleeps_data['hr average'], "HR")
		

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

		self.ST_Sleep_table = ([sleeps_data['total sleep time'], prev_sleeps_data['total sleep time']])
		self.AP_Sleep_table = ([sleeps_data['apnea'], prev_sleeps_data['apnea']])




		self.database.SM.load_SleepMat(time = sleeps_data['date'], bd = sleeps_data['breathing disturbances'], dsd = sleeps_data['deep sleep duration'], dts = sleeps_data['duration to sleep'],
									dtw = sleeps_data['duration to wakeup'], hr = sleeps_data['hr average'], lsd = sleeps_data['light sleep duration'], rsd = sleeps_data['rem sleep duration'], 
									rr = sleeps_data['rr average'], ss = sleeps_data['sleep score'], wpc = sleeps_data['wake up count'], wpd = sleeps_data['wake up duration'])

		self.graph.plot_bar(sleeps_data['date'],sleeps_data['apnea'])

		self.graph.plot_stacked_bar(sleeps_data['date'],sleeps_data['total sleep time'],sleeps_data['awake in bed'],sleeps_data['out of bed count'], sleeps_data['wake up count'])




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
