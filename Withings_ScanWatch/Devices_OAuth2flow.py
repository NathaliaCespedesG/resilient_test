import sys
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from withings_api import WithingsAuth, WithingsApi, AuthScope
from withings_api.common import GetSleepField, GetSleepSummaryField, get_measure_value, MeasureType, CredentialsType, MeasureGetActivityResponse, AuthFailedException
import arrow
import time
import numpy as np
import math
import json
from datetime import timedelta, datetime



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
		self.dates()

		

		self.graph = graph.Graph_generator(start_date =self.initial_dates,
										   end_date = self.ending_dates)


		# Inputs: client_id, consumer_secret, callback_uri
		# Take into account that this inputs will be created after you
		# create your developer account

		self.client_id = client_id
		self.costumer_secret = costumer_secret
		self.callback_uri = callback_uri

		#Create an ID for each user

		self.id_user = input('Please provide the id for the user: ')

		self.database.register(user = self.id_user)


		#Create the credentials File
		# This file has the authorization and refresh token which are
		# used to acquire the data fromo Withings server 

		self.base_path = path.dirname(os.path.abspath(__file__))
		additional_path = "db/General"
		credentials_path = ".credentials"

		self.final_path = path.abspath(path.join(self.base_path, additional_path, self.id_user, credentials_path))

		time.sleep(0.5)

		self.CREDENTIALS_FILE: Final = self.final_path
		

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

		self.ending_day_c = -1
		self.starting_day_c = self.ending_day_c - 6
		self.ending_day_p = self.starting_day_c -1
		self.starting_day_p = self.ending_day_p -6

		#print(arrow.utcnow().shift(days = self.ending_day_c))
		#print(arrow.utcnow().shift(days = self.starting_day_c))
		#print(arrow.utcnow().shift(days = self.ending_day_p))
		#print(arrow.utcnow().shift(days = self.starting_day_p))

		# Dates
		self.initial_dates = arrow.utcnow().shift(days = self.starting_day_c)
		self.initial_dates_rep = self.initial_dates.format('D-MMM-YYYY')
		#print('Initial_Dates from main', self.initial_dates)
		self.initial_dates_table = self.initial_dates.format('D MMM ')


		self.ending_dates = arrow.utcnow().shift(days = self.ending_day_c)
		self.ending_dates_table = self.ending_dates.format('D MMM ')


		self.database.SM.set_date_report(date = self.initial_dates_rep)


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

		#Getting battery from devices
		self.battery = [i['battery'] for i in devices]
		#print("battery from devices", battery)



		self.database.SM.load_SensorInfo(sensor = type_d, hash_deviceid = hash_deviceid, MAC_address = MAC_address)

	def create_nonce(self):

		# This function generates the nonce. The nonce is a signature used
		# to sign requests and it is used by some Withings services.

		signature = self.api.get_signature()
		self.nonce = signature['body']['nonce']
		#print('nonce', self.nonce)


	def data_cleaning(self, x, y):

		y = np.array(y, dtype=float)
		y[np.isnan(y)] = np.nan

		#This function is to clean the data from none or 0 values and convert x to timestamps
		#As withings has different ways to format the dates this function will set all dates to datetime variables

		y[y == None] = np.nan
		y[y == 0] = np.nan
		y[y == -1] = np.nan

		# Check if all elements in the array are of Arrow type

		all_are_arrows = all(isinstance(variable, arrow.Arrow) for variable in x)

		if all_are_arrows:

			x = [arrow_datetime.datetime for arrow_datetime in x]

		return(x,y)


	def unique_values_sleep(self, dates, start_date, end_date, values):


		dates = [datetime.fromtimestamp(a.timestamp()) for a in dates]
		start_date = [arrow_datetime.datetime for arrow_datetime in start_date]
		end_date = [arrow_datetime.datetime for arrow_datetime in end_date]
		
		# Convert date strings to NumPy datetime64
		x = np.array(dates, dtype='datetime64')
		x1 = np.array(start_date, dtype='datetime64')
		x2 = np.array(end_date, dtype='datetime64')

		# Convert values to NumPy array
		y = np.array(values)
		# Calculate the difference between the startdate and enddate
		m = (x2 - x1)

		#print(m)
		#print(values)

		# Leave the values where the difference is the higher one
		max_m_per_date = {}
		positions = []
		for i in range(len(x)):
			date = x[i]
			if date not in max_m_per_date or m[i] > m[max_m_per_date[date]]:
				max_m_per_date[date] = i
		# Create new arrays with unique dates and corresponding maximum m values
		unique_dates = []
		unique_y = []
		for date, max_m in max_m_per_date.items():
			unique_dates.append(date)
			unique_y.append(values[max_m])

		positions = list(max_m_per_date.values())

		return(unique_dates, unique_y, positions)


	def activity_data(self): 

		# This function returns the activity data. Please refer
		# to the withings API documentation to see what type of data
		# you can get from this service.

		self.activity_data = {}
		self.pre_activity_data = {}
		self.month_activity_data = {}
	

		self.meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=self.starting_day_c), enddateymd = arrow.utcnow().shift(days= self.ending_day_c))
		self.prev_meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=self.starting_day_p), enddateymd = arrow.utcnow().shift(days= self.ending_day_p))
		self.monthly_activity = self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=self.starting_day_c - 30), enddateymd = arrow.utcnow().shift(days= self.ending_day_c))
		#print(self.meas_activity)
		#Current Week
		self.activity_data['date'] = [arrow.get(x.date) for x in self.meas_activity.activities]
		self.activity_data['heart_rate'] = [x.hr_average for x in self.meas_activity.activities]
		self.activity_data['date'], self.activity_data['heart_rate'] =self.data_cleaning(self.activity_data['date'],self.activity_data['heart_rate'])
		self.activity_data['calories'] = [x.totalcalories for x in self.meas_activity.activities]
		self.activity_data['date'], self.activity_data['calories'] =self.data_cleaning(self.activity_data['date'],self.activity_data['calories'])
		self.activity_data['steps'] = [x.steps for x in self.meas_activity.activities]
		self.activity_data['date'], self.activity_data['steps'] =self.data_cleaning(self.activity_data['date'],self.activity_data['steps'])
		self.activity_data['hr_min'] = [x.hr_min for x in self.meas_activity.activities]
		self.activity_data['date'], self.activity_data['hr_min'] =self.data_cleaning(self.activity_data['date'],self.activity_data['hr_min'])
		self.activity_data['hr_max'] = [x.hr_max for x in self.meas_activity.activities]
		self.activity_data['date'], self.activity_data['hr_max'] =self.data_cleaning(self.activity_data['date'],self.activity_data['hr_max'])

		self.intra_activitydata(type_time = "current")

		#print(self.meas_activity)

		#Previous Week
		self.pre_activity_data['heart_rate'] = [x.hr_average for x in self.prev_meas_activity.activities]
		self.pre_activity_data['steps'] = [x.steps for x in self.prev_meas_activity.activities]
		#Monthly (4 Weeks) activity
		self.month_activity_data['heart_rate'] = [x.hr_average for x in self.monthly_activity.activities]
		self.month_activity_data['steps'] = [x.steps for x in self.monthly_activity.activities]

		#print(self.activity_data['heart_rate'])

		self.graph.plot_bar(self.activity_data['date'],self.activity_data['steps'])

	def intra_activitydata(self, type_time = None):


		activity_data = {}
		watch_data = []
		HR_watch = []
		Steps_watch = []
		Calories_watch = []
		dates_hr = []
		dates = []
		dates_steps = []
		dates_s = []
		dates_calories = []
		dates_c = []
		HR = []
		mean_HR = []
		dates_to_test = {}
		hr_to_test = {}
		if type_time == "current":
			starting_day = self.starting_day_c 
			ending_day = self.ending_day_c
			#print('Endind date', ending_day)

		if type_time == "prev":
			starting_day = self.starting_day_p
			ending_day = self.ending_day_p
		
		week_days = list(range(starting_day, ending_day))
		week_days.append(week_days[-1]+1)
		#print(week_days)

		total = abs(starting_day) - abs(ending_day)


		for i in range (len(week_days)):

			#print('date 1', arrow.utcnow().shift(days= week_days[i]).replace(hour=0, minute=0, second=0))
			#print('date2', arrow.utcnow().shift(days = week_days[i]+1).replace(hour=0, minute=0, second=0) )

			self.meas_intraactivity = self.api.measure_get_intraactivity(startdate= arrow.utcnow().shift(days= week_days[i]).replace(hour=0, minute=0, second=0), enddate=arrow.utcnow().shift(days = week_days[i]+1).replace(hour=0, minute=0, second=0))
			dates = [key for key, sub_dict in self.meas_intraactivity['series'].items() if 'heart_rate' in sub_dict]
			watch_data = [sub_dict['heart_rate'] for sub_dict in self.meas_intraactivity['series'].values() if 'heart_rate' in sub_dict]
			dates_s = [key for key, sub_dict in self.meas_intraactivity['series'].items() if 'steps' in sub_dict]
			step_watch_data = [sub_dict['steps'] for sub_dict in self.meas_intraactivity['series'].values() if 'steps' in sub_dict]
			dates_c = [key for key, sub_dict in self.meas_intraactivity['series'].items() if 'calories' in sub_dict]
			calories_watch_data = [sub_dict['calories'] for sub_dict in self.meas_intraactivity['series'].values() if 'calories' in sub_dict]
			dates_to_test[i] = dates
			hr_to_test[i] = watch_data
			dates_hr.append(dates)
			#print(np.mean(watch_data))
			HR_watch.append(watch_data)
			dates_steps.append(dates_s)
			Steps_watch.append(step_watch_data)
			dates_calories.append(dates_c)
			Calories_watch.append(calories_watch_data)


	
		#self.small_test(dates_to_test)

		HR_watch = sum(HR_watch,[])
		Steps_watch = sum(Steps_watch,[])
		Calories_watch = sum(Calories_watch,[])
		#dates_db_a = sum(dates_db_a, [])
		dates_hr = sum(dates_hr,[])
		dates_hr_1 = [int(x) for x in dates_hr]
		dates_steps = sum(dates_steps,[])
		#dates_steps = [int(x) for x in dates_steps]
		dates_calories = sum(dates_calories,[])
		#dates_calories = [int(x) for x in dates_calories]

		if type_time == "current":
			start_dates_hr = self.wakeup_hours
			end_dates_hr = self.fellasleep_hours
			self.hr_based_sleep = self.hr_average_basedon_sleep(dates = dates_to_test, HR = hr_to_test, startdates = start_dates_hr, enddates = end_dates_hr )
			#self.final_hr = self.backup_data(value1 = self.activity_data['heart_rate'], value2 = self.hr_based_sleep)
			self.graph.plot_scatter(x = dates_hr_1, y = HR_watch, k = self.activity_data['date'], j = self.hr_based_sleep, name = "HR_ScanWatch")
			self.database.SM.load_intra_activity(hr = HR_watch, time = dates_hr, time_steps = dates_steps, steps = Steps_watch, time_calories = dates_calories, calories = Calories_watch)
			self.database.SM.load_ScanWatch(hr = self.hr_based_sleep, calories = self.activity_data['calories'], steps = self.activity_data['steps'],  time = self.activity_data['date'] )


		if type_time == "prev":
			start_dates_hr = self.wakeup_hours_prev
			end_dates_hr = self.fellasleep_hours_prev
			self.hr_based_sleep_prev = self.hr_average_basedon_sleep(dates = dates_to_test, HR = hr_to_test, startdates = start_dates_hr, enddates = end_dates_hr )
			return(self.hr_based_sleep_prev)
	def hr_average_basedon_sleep(self, dates = None, HR = None, startdates = None, enddates = None):

		# Initialize a dictionary to store mean HR values for each key
		mean_hr_dict = {}

		# Iterate through keys in the 'dates' dictionary
		for key in dates:
			timestamps = [int(ts) for ts in dates[key]]
			hr_values = HR[key]

			# Get the corresponding start and end dates for this key using the key index
			startdate = startdates[key].replace(tzinfo='UTC')
			enddate = enddates[key].replace(tzinfo='UTC')

			# Convert startdate and enddate to timestamps
			startdate_ts = startdate.timestamp()
			enddate_ts = enddate.timestamp()

			# Initialize a list to store HR values within the date range for this key
			hr_values_within_range = []

			# Iterate through timestamps and HR values for this key
			for timestamp, hr in zip(timestamps, hr_values):
				
				if startdate_ts <= timestamp <= enddate_ts:
					hr_values_within_range.append(hr)

			# Calculate the mean of HR values within the date range for this key
			if hr_values_within_range:
				mean_hr = sum(hr_values_within_range) / len(hr_values_within_range)
				mean_hr_dict[key] = mean_hr
			else:
				# If no HR values found within the specified date range, set the mean to None
				mean_hr_dict[key] = None

			
			rounded_values_list = [round(value)  if value is not None else None for value in mean_hr_dict.values()]

		#print(rounded_values_list)
		return(rounded_values_list)


	def scale_data(self):

		scale_data = {}
		prev_scale_data = {}
		monthly_scale_data = {}


		scale_starting_date = arrow.utcnow().shift(days= self.ending_day_c - 6)
		scale_ending_date = arrow.utcnow().shift(days = self.ending_day_c)

		self.meas_current = self.api.measure_get_meas(startdate=arrow.utcnow().shift(days= self.starting_day_c), enddate = arrow.utcnow().shift(days= self.ending_day_c), lastupdate = None)
		self.meas_prev = self.api.measure_get_meas(startdate=arrow.utcnow().shift(days= self.starting_day_p), enddate = arrow.utcnow().shift(days= self.ending_day_p), lastupdate = None)
		self.meas_monthly = self.api.measure_get_meas(startdate = arrow.utcnow().shift(days= self.ending_day_c - 30), enddate = arrow.utcnow().shift(days= self.ending_day_c), lastupdate = None)

		#Current week values
		scale_data['date'] = [arrow.get(x.date) for x in self.meas_current.measuregrps]
		scale_data['measures'] = [x.measures for x in self.meas_current.measuregrps]
		self.weight, muscle_mass, bone_mass, fat_mass, hydration = self.scale_data_extractor(scale_data['measures'])
		#Cleaning data for the table
		scale_data['date'], self.weight =self.data_cleaning(scale_data['date'],self.weight)

		#Prev week values
		prev_scale_data['date'] = [arrow.get(x.date) for x in self.meas_prev.measuregrps]
		prev_scale_data['measures'] = [x.measures for x in self.meas_prev.measuregrps]
		self.weight_p, muscle_mass_p, bone_mass_p, fat_mass_p, hydration_p = self.scale_data_extractor(prev_scale_data['measures'])
		#Cleaning data for the table
		prev_scale_data['date'], self.weight_p =self.data_cleaning(prev_scale_data['date'],self.weight_p)

		#Monthly values
		monthly_scale_data['date'] = [arrow.get(x.date) for x in self.meas_monthly.measuregrps]

		#Graph x titles dates
		scale_starting_date = monthly_scale_data['date'][-1]
		scale_ending_date = monthly_scale_data['date'][0]

		monthly_scale_data['measures'] = [x.measures for x in self.meas_monthly.measuregrps]
	
		self.weight_m, muscle_mass_m, bone_mass_m, fat_mass_m, hydration_m = self.scale_data_extractor(monthly_scale_data['measures'])

		#Cleaning data for the table
		monthly_scale_data['date'], self.weight_m = self.data_cleaning(monthly_scale_data['date'], self.weight_m)
		monthly_scale_data['date_mm'], muscle_mass_m = self.data_cleaning(monthly_scale_data['date'], muscle_mass_m)
		monthly_scale_data['date_bm'], bone_mass_m = self.data_cleaning(monthly_scale_data['date'], bone_mass_m)
		monthly_scale_data['date_fm'], fat_mass_m = self.data_cleaning(monthly_scale_data['date'], fat_mass_m)
		monthly_scale_data['date_h'], hydration_m = self.data_cleaning(monthly_scale_data['date'], hydration_m)

		self.database.SM.load_Scale(time = scale_data['date'], weight = self.weight, muscle_mass = muscle_mass, bone_mass = bone_mass, fat_mass = fat_mass)

		
		self.graph.plot_continous(monthly_scale_data['date'],self.weight_m, monthly_scale_data['date_mm'], muscle_mass_m, monthly_scale_data['date_bm'],bone_mass_m,
								  monthly_scale_data['date_fm'], fat_mass_m, monthly_scale_data['date_h'], hydration_m, scale_starting_date, scale_ending_date, "Scale")
		
	def scale_data_extractor(self, data):

		# Initialize dictionaries for each measurement type

		measurement_types = {
		"weight": [],
		"fat_mass": [],
		"muscle_mass": [],
		"hydration": [],
		"bone_mass": [],}

		for data_tuple in data:
			weight_value = None
			fat_mass_value = None
			muscle_mass_value = None
			hydration_value = None
			bone_mass_value = None

			for measure in data_tuple:

				if measure.type == MeasureType.WEIGHT:
					weight_value = measure.value * (10 ** measure.unit)
				elif measure.type == MeasureType.FAT_MASS_WEIGHT:
					fat_mass_value = measure.value * (10 ** measure.unit)
				elif measure.type == MeasureType.MUSCLE_MASS:
					muscle_mass_value = measure.value * (10 ** measure.unit)
				elif measure.type == MeasureType.HYDRATION:
					hydration_value = measure.value * (10 ** measure.unit)
				elif measure.type == MeasureType.BONE_MASS:
					bone_mass_value = measure.value * (10 ** measure.unit)

			# Append values to their respective lists or np.nan if missing
			measurement_types["weight"].append(weight_value)
			measurement_types["fat_mass"].append(fat_mass_value)
			measurement_types["muscle_mass"].append(muscle_mass_value)
			measurement_types["hydration"].append(hydration_value)
			measurement_types["bone_mass"].append(bone_mass_value)


		# List for measurements
		weight = np.array(measurement_types["weight"])
		fat_mass = np.array(measurement_types["fat_mass"])
		muscle_mass = np.array(measurement_types["muscle_mass"])
		hydration = np.array(measurement_types["hydration"])
		bone_mass = np.array(measurement_types["bone_mass"])

		return(weight, muscle_mass, bone_mass, fat_mass, hydration)


	def str_to_float(self, number, unit):

		number = str(number)
		number = number[:unit] + "." + number[unit:] 
		number = float(number)

		return(number)


		
	def sleep(self):

		sleephf_data = {}

		sleeps_data = {}

		sleepbu_data = {}

		sleepbu_data_p = {}

		prev_sleeps_data = {}

		month_sleeps_data = {}

		self.get_sleep = self.api.sleep_get(data_fields=GetSleepField,startdate=arrow.utcnow().shift(days= self.starting_day_c+1), enddate=arrow.utcnow().shift(days= self.starting_day_c+2),)
		
		sleephf_data['start_date'] = [arrow.get(x['startdate']) for x in self.get_sleep['series']]
		sleephf_data['end_date'] = [arrow.get(x['enddate']) for x in self.get_sleep['series']]
		sleephf_data['state'] = [x['state'] for x in self.get_sleep['series']]

		#self.graph.plot_events(sleephf_data['start_date'], sleephf_data['end_date'], sleephf_data['state'])


		self.sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days = self.starting_day_c),enddateymd=arrow.utcnow().shift(days = self.ending_day_c), lastupdate = None)
		self.prev_sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days = self.starting_day_p),enddateymd=arrow.utcnow().shift(days= self.ending_day_p), lastupdate = None)
		self.month_sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days = self.starting_day_c-30),enddateymd=arrow.utcnow().shift(days= self.ending_day_c), lastupdate = None)
		
		#print(self.sleep_summary)


		sleeps_data['date'] = [arrow.get(x.date) for x in self.sleep_summary.series]
		sleeps_data['start_date'] = [arrow.get(x.startdate) for x in self.sleep_summary.series]
		sleeps_data['end_date'] = [arrow.get(x.enddate) for x in self.sleep_summary.series]
		sleeps_data['data'] = [x.data for x in self.sleep_summary.series]

		prev_sleeps_data['date'] = [arrow.get(x.date) for x in self.prev_sleep_summary.series]
		prev_sleeps_data['start_date'] = [arrow.get(x.startdate) for x in self.prev_sleep_summary.series]
		prev_sleeps_data['end_date'] = [arrow.get(x.enddate) for x in self.prev_sleep_summary.series]
		prev_sleeps_data['data'] = [x.data for x in self.prev_sleep_summary.series]

		month_sleeps_data['date'] = [arrow.get(x.date) for x in self.month_sleep_summary.series]
		month_sleeps_data['start_date'] = [arrow.get(x.startdate) for x in self.month_sleep_summary.series]
		month_sleeps_data['end_date'] = [arrow.get(x.enddate) for x in self.month_sleep_summary.series]
		month_sleeps_data['data'] = [x.data for x in self.month_sleep_summary.series]

			# Values of HR and RR for the table

		
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

		# Monthly week values
		month_sleeps_data['hr average'] = [x.hr_average for x in month_sleeps_data['data']]
		month_sleeps_data['rr average'] = [x.rr_average for x in month_sleeps_data['data']]
		month_sleeps_data['total sleep time'] = [x.total_sleep_time for x in month_sleeps_data['data']]
		month_sleeps_data['apnea'] = [x.apnea_hypopnea_index for x in month_sleeps_data['data']]

		#Unique values calculation (The values for the variables are the ones taken between the biggest difference from start date and end date)

		self.current_dates_ss, self.current_heart_rate, _ = self.unique_values_sleep(sleeps_data['date'], sleeps_data['start_date'], sleeps_data['end_date'], sleeps_data['hr average']) 
		previous_dates_ss, self.prev_heart_rate, _ = self.unique_values_sleep(prev_sleeps_data['date'], prev_sleeps_data['start_date'], prev_sleeps_data['end_date'], prev_sleeps_data['hr average'])
		monthly_dates_ss, self.monthly_heart_rate, _ = self.unique_values_sleep(month_sleeps_data['date'], month_sleeps_data['start_date'], month_sleeps_data['end_date'], month_sleeps_data['hr average'])  

		self.current_dates_ss, self.current_rr, _ = self.unique_values_sleep(sleeps_data['date'], sleeps_data['start_date'], sleeps_data['end_date'], sleeps_data['rr average']) 
		previous_dates_ss, self.prev_rr, _ = self.unique_values_sleep(prev_sleeps_data['date'], prev_sleeps_data['start_date'], prev_sleeps_data['end_date'], prev_sleeps_data['rr average'])
		monthly_dates_ss, self.monthly_rr, _ = self.unique_values_sleep(month_sleeps_data['date'], month_sleeps_data['start_date'], month_sleeps_data['end_date'], month_sleeps_data['rr average'])  


		#Values  of total time in bed, awake in bed conversion to hours /3600 
		sleeps_data['total sleep time']=[x/3600 for x in sleeps_data['total sleep time']]
		sleeps_data['awake in bed']=[x/3600 for x in sleeps_data['awake in bed']]
		prev_sleeps_data['total sleep time']=[x/3600 for x in prev_sleeps_data['total sleep time']]
		month_sleeps_data['total sleep time'] =[x/3600 for x in month_sleeps_data['total sleep time']]


		#This is to calculate the woke up and fell asleep times 
		sleep_summary_backup = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days = self.starting_day_c),enddateymd=arrow.utcnow().shift(days = self.ending_day_c + 1), lastupdate = None)
		sleepbu_data['date'] = [arrow.get(x.date) for x in sleep_summary_backup.series]
		sleepbu_data['start_date'] = [arrow.get(x.startdate) for x in sleep_summary_backup.series]
		sleepbu_data['end_date'] = [arrow.get(x.enddate) for x in sleep_summary_backup.series]
		sleepbu_data['data'] = [x.data for x in sleep_summary_backup.series]
		sleepbu_data['night_events'] = [x.night_events for x in sleepbu_data['data']]
		current_dates_ne, current_events, positions = self.unique_values_sleep(sleepbu_data['date'], sleepbu_data['start_date'], sleepbu_data['end_date'], sleepbu_data['night_events'])
		
		#This is to calculate the woke up and fell asleep times - PREVIOUS
		sleep_summary_backup_p = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days = self.starting_day_p),enddateymd=arrow.utcnow().shift(days = self.ending_day_p + 1), lastupdate = None)
		sleepbu_data_p['date'] = [arrow.get(x.date) for x in sleep_summary_backup_p.series]
		sleepbu_data_p['start_date'] = [arrow.get(x.startdate) for x in sleep_summary_backup_p.series]
		sleepbu_data_p['end_date'] = [arrow.get(x.enddate) for x in sleep_summary_backup_p.series]
		sleepbu_data_p['data'] = [x.data for x in sleep_summary_backup_p.series]
		sleepbu_data_p['night_events'] = [x.night_events for x in sleepbu_data_p['data']]
		
		prev_dates_ne, prev_events, positions_prev = self.unique_values_sleep(sleepbu_data_p['date'], sleepbu_data_p['start_date'], sleepbu_data_p['end_date'], sleepbu_data_p['night_events'])

		self.daily_dates(startdate = sleepbu_data['start_date'], enddate = sleepbu_data['end_date'], positions = positions)		
		self.daily_dates_prev(startdate = sleepbu_data_p['start_date'], enddate = sleepbu_data_p['end_date'], positions = positions_prev)

		
		# Unique values Total Sleep Time - Graph and Table
		self.current_dates_ss, self.current_sleep_time, _ = self.unique_values_sleep(sleeps_data['date'], sleeps_data['start_date'], sleeps_data['end_date'], sleeps_data['total sleep time']) 
		self.previous_dates_ss, self.prev_sleep_time, _ = self.unique_values_sleep(prev_sleeps_data['date'], prev_sleeps_data['start_date'], prev_sleeps_data['end_date'], prev_sleeps_data['total sleep time'])
		self.monthly_dates_ss, self.monthly_sleep_time, _ = self.unique_values_sleep(month_sleeps_data['date'], month_sleeps_data['start_date'], month_sleeps_data['end_date'], month_sleeps_data['total sleep time'])  

		# Unique values Awake in bed - Out of bed count (This values are only used in the graph)
		current_dates_ab, current_awake_bed, _ = self.unique_values_sleep(sleeps_data['date'], sleeps_data['start_date'], sleeps_data['end_date'], sleeps_data['awake in bed']) 
		current_dates_ab, current_out_bed, _ = self.unique_values_sleep(sleeps_data['date'], sleeps_data['start_date'], sleeps_data['end_date'], sleeps_data['out of bed count']) 

		# Unique values for Sleep Apnoea - Graph and Table
		self.current_dates_ss, self.current_apnea, _ = self.unique_values_sleep(sleeps_data['date'], sleeps_data['start_date'],  sleeps_data['end_date'], sleeps_data['apnea']) 
		self.current_dates_ss, self.current_apnea = self.data_cleaning(self.current_dates_ss, self.current_apnea)

		#print('APNEAAAA', self.current_apnea)

		self.previous_dates_ss, self.prev_apnea, _ = self.unique_values_sleep(prev_sleeps_data['date'], prev_sleeps_data['start_date'], prev_sleeps_data['end_date'], prev_sleeps_data['apnea'])
		self.previous_dates_ss, self.prev_apnea = self.data_cleaning(self.previous_dates_ss, self.prev_apnea)

		self.monthly_dates_ss, self.monthly_apnea, _ = self.unique_values_sleep(month_sleeps_data['date'], month_sleeps_data['start_date'], month_sleeps_data['end_date'], month_sleeps_data['apnea'])  
		self.monthly_dates_ss, self.monthly_apnea = self.data_cleaning(self.monthly_dates_ss, self.monthly_apnea)


		#print('Sleep Apnoea', self.current_apnea)	
		self.database.SM.load_SleepMat(time = sleeps_data['date'], bd = sleeps_data['breathing disturbances'], dsd = sleeps_data['deep sleep duration'], dts = sleeps_data['duration to sleep'],
									dtw = sleeps_data['duration to wakeup'], hr = sleeps_data['hr average'], lsd = sleeps_data['light sleep duration'], rsd = sleeps_data['rem sleep duration'], 
									rr = sleeps_data['rr average'], ss = sleeps_data['sleep score'], wpc = sleeps_data['wake up count'], wpd = sleeps_data['wake up duration'])

		#self.graph.plot_bar(sleeps_data['date'],sleeps_data['apnea'])

		self.graph.plot_stacked_bar(x = self.current_dates_ss, y = self.current_sleep_time,
									z = current_awake_bed, o = current_out_bed)





	def daily_dates(self, startdate = None, enddate = None, positions = None):

		start_dates = [startdate[i] for i in positions]
		end_dates = [enddate[i] for i in positions]

		self.wakeup_hours = end_dates[:-1]
		self.fellasleep_hours = start_dates[1:]
		#print(self.wakeup_hours)
		#print(self.fellasleep_hours)

	def daily_dates_prev(self, startdate = None, enddate = None, positions = None):
		start_dates = [startdate[i] for i in positions]
		end_dates = [enddate[i] for i in positions]

		self.wakeup_hours_prev = end_dates[:-1]
		self.fellasleep_hours_prev = start_dates[1:]





	def sleep_daily(self):

		sleephf_data = []
		sleephf_data_hr = []
		sleephf_data_snoring = []
		sleephf_data_sdnn = []
		sleephf_startdate = []
		sleephf_enddate = []
		sleephf_state = []
		data = []
		data_hr = []
		data_snoring = []
		data_sdnn = []
		data_startdate = []
		data_enddate = []
		data_states = []
		HR_sleep = []
		starting_day = self.starting_day_c
		ending_day = self.ending_day_c
		mean_hr = []
		mean_rr = []
		self.usage = {}

		sleeps_data = {}

		week_days = list(range(starting_day, ending_day))
		week_days.append(-1)
		total = abs(starting_day) - abs(ending_day)

		for i in range (len(week_days)):
			all_values = []
			all_values_hr = []
			count_hr = 0
			mean_1 = 0
			count = 0
			mean = 0

			self.get_sleep_1 = self.api.sleep_get(data_fields=GetSleepField,startdate=arrow.utcnow().shift(days= week_days[i]).replace(hour=0, minute=0, second=0), enddate=arrow.utcnow().shift(days = week_days[i]+1).replace(hour=0, minute=0, second=0),)
			
			#print(self.get_sleep_1)
			try:
				#Respiration rate
				sleephf_data = [x['rr'] for x in self.get_sleep_1['series']]
				print('--------------------------------------------------------')
				all_values = [value for data_dict in sleephf_data for value in data_dict.values()]
				all_dates = [value for data_dict in sleephf_data for value in data_dict.keys()]
				#print(self.get_sleep_1)
				count = len(all_values)  # Get the count of values
				mean = sum(all_values) / count if count > 0 else None
				#Heart rate 
				sleephf_data_hr = [x['hr'] for x in self.get_sleep_1['series']]
				all_values_hr = [value for data_dict in sleephf_data_hr for value in data_dict.values()]
				count_hr = len(all_values_hr)  # Get the count of values
				mean_1 = sum(all_values_hr) / count if count > 0 else None

				#snoring
				sleephf_data_snoring = [x['snoring'] for x in self.get_sleep_1['series']]
				#sdnn_1
				sleephf_data_sdnn = [x['sdnn_1'] for x in self.get_sleep_1['series']]
				#start_date
				sleephf_startdate = [x['startdate'] for x in self.get_sleep_1['series']]
				#end_date
				sleephf_enddate = [x['enddate'] for x in self.get_sleep_1['series']]
				#state
				sleephf_state = [x['state'] for x in self.get_sleep_1['series']]

				#Arrays with all the values from each measurement
				data.append(sleephf_data)
				data_hr.append(sleephf_data_hr)
				data_snoring.append(sleephf_data_snoring)
				data_sdnn.append(sleephf_data_sdnn)
				data_startdate.append(sleephf_startdate)
				data_enddate.append(sleephf_enddate)
				data_states.append(sleephf_state)

				
				mean_rr.append(round(mean))
				mean_hr.append(round(mean_1))

			except:
				print("Missing sleep data")

		
		#print('usage', self.usage)

		# This data represent Respiration Rate 'rr' in the withings structure

		data = sum(data,[])
		dates = [i for s in [d.keys() for d in data] for i in s]
		dates = [int(x) for x in dates]
		RR = [i for s in [d.values() for d in data] for i in s]


		# This data represent Heart Rate 'hr' in the withings structure

		data_hr = sum(data_hr,[])
		dates_hr = [i for s in [d.keys() for d in data_hr] for i in s]
		dates_hr = [int(x) for x in dates_hr]
		HR = [i for s in [d.values() for d in data_hr] for i in s]

		#This data respresent Snoring 'snoring' in the withings structute
		data_snoring = sum(data_snoring,[])
		dates_snoring = [i for s in [d.keys() for d in data_snoring] for i in s]
		dates_snoring = [int(x) for x in dates_snoring]
		snoring = [i for s in [d.values() for d in data_snoring] for i in s]


		#This data respresent Heart rate variability 'sdnn_1' in the withings structute

		data_sdnn = sum(data_sdnn,[])
		dates_sdnn = [i for s in [d.keys() for d in data_sdnn] for i in s]
		dates_sdnn = [int(x) for x in dates_sdnn]
		sdnn_1 = [i for s in [d.values() for d in data_sdnn] for i in s]

		#Start dates
		data_startdate = sum(data_startdate,[])
		data_enddate = sum(data_enddate,[])
		data_states = sum(data_states,[])




		# Backup funtion in case sleep summary service is not updating the average of hr and rr per night
		self.rr_mean_bu = self.backup_data(value1 = mean_rr, value2 = self.current_rr)
		self.hr_mean_bu = self.backup_data(value1 = mean_hr, value2 = self.current_heart_rate)
		#print(self.hr_mean_bu)


		self.graph.plot_scatter(x = dates, y = RR , k = self.current_dates_ss, j = self.rr_mean_bu, name = "RR")
		self.graph.plot_scatter(x = dates_hr, y = HR , k = self.current_dates_ss,  j = self.hr_mean_bu, name = "HR")

		self.database.SM.load_intra_sleep(start_date = data_startdate, end_date = data_enddate, ss = data_states, hr = HR, hr_date = dates_hr,
										rr = RR, rr_date = dates, snoring = snoring, snoring_date = dates_snoring, sdnn_1 = sdnn_1, sdnn_1_date = dates_sdnn)

	# The following function is called when there are higher granularity data but not averages
	def backup_data(self, value1 = None, value2 = None):

		value = [v1 if v2 is None else v2 for v1, v2 in zip(value1, value2)]

		return(value)


	# The following function is to fill the table inf the PDF
	def table_filler(self):
		# Values for the table

		#Sleep
		self.HR_Sleep_table = ([self.hr_mean_bu, self.prev_heart_rate, self.monthly_heart_rate ])
		self.RR_Sleep_table = ([self.rr_mean_bu, self.prev_rr, self.monthly_rr ])
		self.ST_Sleep_table = ([self.current_sleep_time, self.prev_sleep_time, self.monthly_sleep_time])
		#print(self.current_apnea)
		#print(self.prev_apnea)
		self.AP_Sleep_table = ([self.current_apnea, self.prev_apnea, self.monthly_apnea])

		#Scale
		self.Weight_table = (self.weight, self.weight_p, self.weight_m)

		#ScanWatch
		self.prev_hr = self.intra_activitydata(type_time = 'prev')
		self.HR_table = ([self.hr_based_sleep, self.prev_hr, self.month_activity_data['heart_rate']]) 
		self.Steps_table = ([self.activity_data['steps'], self.pre_activity_data['steps'], self.month_activity_data['steps']])

	def usage_levels(self, weekly_usage = None, daily_usage = None):
		pass


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

		self.table_filler()

		self.document_generation = pdf_gen.PDF_generation(day_hr = self.HR_table, 
					night_hr = self.HR_Sleep_table, 
					night_rr = self.RR_Sleep_table,
					steps = self.Steps_table, 
					sleep_duration = self.ST_Sleep_table, 
					sleep_apnoea = self.AP_Sleep_table,
					weight = self.Weight_table,
					c_date = self.initial_dates_table,
					e_date = self.ending_dates_table,
					path = path,
					id_nhs = self.id_user)


	def remove_images(self):

		files_in_folder = os.listdir(


			self.base_path)

		for file_name in files_in_folder:
			file_path = os.path.join(self.base_path, file_name)
			if os.path.isfile(file_path) and file_name.lower().endswith('.png'):
				os.remove(file_path)
				print(f"Removed: {file_name}")
			else:
				print(f"Skipped: {file_name}")






M = Devices_OAuth2flow(client_id = 'e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc', 
		       costumer_secret = 'c2b3bd8f8fa210533aa3e7ef54abd4654d2a44cfe4f33d9f3aff63b4ce0943c4',
		       callback_uri = 'https://40.81.128.68:443')
M.get_user_credentials()
M.devices_info()
M.scale_data()
M.sleep()
M.sleep_daily()
M.activity_data()
#M.intra_activitydata()
#M.table()
M.doc_generation()
M.remove_images()
#M.deactivate_raw_data()
#M.activate_raw_data()
