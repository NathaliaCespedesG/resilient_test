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

		self.meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=-30), enddateymd = arrow.utcnow())
		print('From activity service', self.meas_activity)
		activity_data['date'] = [arrow.get(x.date) for x in self.meas_activity.activities]
		activity_data['heart_rate'] = [x.hr_average for x in self.meas_activity.activities]
		activity_data['calories'] = [x.totalcalories for x in self.meas_activity.activities]
		activity_data['steps'] = [x.steps for x in self.meas_activity.activities]
		activity_data['hr_min'] = [x.hr_min for x in self.meas_activity.activities]
		activity_data['hr_max'] = [x.hr_max for x in self.meas_activity.activities]


		print('average', activity_data['heart_rate'])
		print('minimums', activity_data['hr_min'])
		print('maximums', activity_data['hr_max'])

		self.plot_continous(activity_data['date'],activity_data['calories'],activity_data['steps'],[],[], "ScanWatch")
		self.plot_min_max_av(activity_data['date'],activity_data['heart_rate'],activity_data['hr_min'],activity_data['hr_max'], "ScanWatch", "HR")



		self.database.SM.load_ScanWatch(hr = activity_data['heart_rate'], calories = activity_data['calories'], steps = activity_data['steps'],  time = activity_data['date'] )

		self.meas2 = self.api.measure_get_meas(startdate=arrow.utcnow().shift(days=-35), enddate=arrow.utcnow(), lastupdate = None)

		scale_data['date'] = [arrow.get(x.date) for x in self.meas2.measuregrps]
		scale_data['measures'] = [x.measures for x in self.meas2.measuregrps]




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


		self.database.SM.load_Scale(time = scale_data['date'], weight = weight, muscle_mass = muscle_mass, bone_mass = bone_mass, fat_mass = fat_mass)

		self.plot_continous(scale_data['date'],weight, muscle_mass, bone_mass, fat_mass, "Scale")


	def str_to_float(self, number, unit):

		number = str(number)
		number = number[:unit] + "." + number[unit:] 
		number = float(number)

		return(number)


	


		

	def intra_activitydata(self):
		
		self.meas_intraactivity = self.api.measure_get_intraactivity(startdate = arrow.utcnow().shift(hours=-24), enddate  = arrow.utcnow())
		print('Meas Intraactivity', self.meas_intraactivity)
		print(type(self.meas_intraactivity))
		#self.meas_intraactivity.


	def sleep(self):

		sleephf_data = {}

		sleeps_data = {}

		self.get_sleep = self.api.sleep_get(data_fields=GetSleepField,startdate=arrow.utcnow().shift(days=-25), enddate=arrow.utcnow().shift(days=-24),)
		#print('from sleep', self.get_sleep['series'])
		#print(self.get_sleep['series'])
		sleephf_data['start_date'] = [arrow.get(x['startdate']) for x in self.get_sleep['series']]
		sleephf_data['end_date'] = [arrow.get(x['enddate']) for x in self.get_sleep['series']]
		sleephf_data['state'] = [x['state'] for x in self.get_sleep['series']]
		print(sleephf_data['start_date'])
		#print(sleephf_data['end_date'])
		#print(sleephf_data['state'])


		print(len(sleephf_data['start_date']))
		self.plot_events(sleephf_data['start_date'], sleephf_data['end_date'], sleephf_data['state'])

		


		self.sleep_summary = self.api.sleep_get_summary(data_fields=GetSleepSummaryField, startdateymd=arrow.utcnow().shift(days=-25),enddateymd=arrow.utcnow().shift(days=-1), lastupdate = None)

		#print('Sleep Summary', self.sleep_summary)

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
		sleeps_data['wake up duration'] = [x.wakeupduration for x in sleeps_data['data']]


		self.database.SM.load_SleepMat(time = sleeps_data['date'], bd = sleeps_data['breathing disturbances'], dsd = sleeps_data['deep sleep duration'], dts = sleeps_data['duration to sleep'],
									dtw = sleeps_data['duration to wakeup'], hr = sleeps_data['hr average'], lsd = sleeps_data['light sleep duration'], rsd = sleeps_data['rem sleep duration'], 
									rr = sleeps_data['rr average'], ss = sleeps_data['sleep score'], wpc = sleeps_data['wake up count'], wpd = sleeps_data['wake up duration'])

		self.plot_min_max_av(sleeps_data['date'], sleeps_data['hr average'],sleeps_data['hr_min'],sleeps_data['hr_max'], "SleepMat", "HR")

		self.plot_bar(sleeps_data['date'],sleeps_data['sleep score'])





		



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




	def plot_scatter(self, x, y):

		x = [datetime.fromtimestamp(a.timestamp()) for a in x]

		# Create a scatter plot
		plt.scatter(x, y, marker='o', color='green')

		# Set the x-axis format as dates
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

		# Rotate the x-axis tick labels for better readability (optional)
		plt.gcf().autofmt_xdate()

		# Label the axes and add a title
		plt.xlabel('Date')
		plt.ylabel('HR')
		plt.title('Sleep Mat')

		# Display the plot
		plt.show()


	def plot_min_max_av(self,x_values,y_average,y_min,y_max,device,type_d):

		x_values = [datetime.fromtimestamp(a.timestamp()) for a in x_values]

		# Calculate the range (difference between min and max)

		print(type(y_average[1]))


		y_average = [float('nan') if x == 0 else x for x in y_average]
		y_min = [float('nan') if x == 0 else x for x in y_min]
		y_max = [float('nan') if x == 0 else x for x in y_max]

		y_range = np.array(y_max) - np.array(y_min)

		# Create the figure and axis

		fig, ax = plt.subplots()

		# Plot the average line
		ax.scatter(x_values, y_average, color='blue', label='Average')

		# Plot the error bars (range)
		ax.errorbar(x_values, y_average, yerr=y_range/2, fmt='o', color='blue', ecolor='lightblue', capsize=5, label='Range')

		# Set the x-axis limits

		ax.set_xlim(min(x_values), max(x_values))


		# Add labels and title

		ax.set_xlabel('Date')

		if device == "ScanWatch":

			ax.set_ylabel(type_d)
			ax.set_title('ScanWatch')

		elif device == "SleepMat":
			ax.set_ylabel(type_d)
			ax.set_title('SleepMat')

		# Add legend
		ax.legend()

		# Add average value as text
		for x, y in zip(x_values, y_average):
			ax.text(x, y, f'{y:.2f}', ha='center', va='bottom')

		# Show the plot
		plt.show()


	def plot_continous(self,x,y,z,w,t, device):


		fig, ax = plt.subplots(figsize=(12,8))


		index_0 = [index for index, value in enumerate(y) if value == 0]


		if device == "ScanWatch":



			y = [value for value in y if value != 0]
			z = [value for value in z if value != 0]

			x = [datetime.fromtimestamp(a.timestamp()) for a in x]
			x = [value for index, value in enumerate(x) if index not in index_0]

			# Create a scatter plot
			plt.plot(x, y, '-ok', color='purple', label = 'Calories')
			plt.plot(x, z, '-ok', color='blue', label = 'Steps')

			# Set the x-axis format as dates
			plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

			# Rotate the x-axis tick labels for better readability (optional)
			plt.gcf().autofmt_xdate()

			for index in range(len(x)):
				ax.text(x[index], y[index], y[index], size=8)
				ax.text(x[index], z[index], z[index], size=8)

			plt.title('ScanWatch')

		elif device == "Scale":


			y = [value for value in y if value != 0]
			z = [value for value in z if value != 0]
			w = [value for value in w if value != 0]
			t = [value for value in t if value != 0]

			x = [datetime.fromtimestamp(a.timestamp()) for a in x]
			x = [value for index, value in enumerate(x) if index not in index_0]

			# Create a scatter plot
			plt.plot(x, y, '-ok', color='purple', label = 'Calories')
			plt.plot(x, z, '-ok', color='blue', label = 'Muscle mass')
			plt.plot(x, w, '-ok', color='green', label = 'Bone mass')
			plt.plot(x, t, '-ok', color='orange', label = 'Fat mass')

			# Set the x-axis format as dates
			plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

			# Rotate the x-axis tick labels for better readability (optional)
			plt.gcf().autofmt_xdate()

			for index in range(len(x)):
				ax.text(x[index], y[index], y[index], size=8)
				ax.text(x[index], z[index], z[index], size=8)
				ax.text(x[index], w[index], z[index], size=8)
				ax.text(x[index], t[index], z[index], size=8)

			plt.title('Scale')


		# Label the axes and add a title
		plt.xlabel('Date')
		plt.ylabel('Data')
		

		# Display the plot
		plt.legend()
		plt.show()


	def plot_bar(self,x,y):

		# Convert Arrow datetime objects to strings

		x_labels = [a.format('YYYY-MM-DD') for a in x]

		colors = ["red" if i < 60 else "green" for i in y]

		# Create a bar plot

		plt.bar(x_labels, y, color = colors)

		# Label the axes and add a title

		plt.xlabel('Date')
		plt.ylabel('Sleep Score')
		plt.title('Sleep Mat')

		# Display the plot
		plt.show()


	def plot_events(self,start_times, end_times, amplitudes):

		# Create a figure and axis
		fig, ax = plt.subplots()

		rect2 = []

		print(start_times)


		# x_limit calculation
		x_lim_min = min(start_times)
		print('Min date', x_lim_min)
		x_lim_max = max(end_times)
		print('Min date', x_lim_max)

		
		legend_handles = {}

		# Loop through each event and plot the colored rectangle

		for start_time, end_time, amplitude in zip(start_times, end_times, amplitudes):

			# Convert start and end times to datetime objects
			start_datetime = start_time.datetime
			start_datetime = mdates.date2num(start_datetime)

			print(start_datetime)

			end_datetime = end_time.datetime
			end_datetime = mdates.date2num(end_datetime)
			print(end_datetime)

			# Calculate the duration of the event in minutes (as an integer)
			width = end_datetime - start_datetime

			
			# Create a rectangle patch for the event
			print(amplitude)
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



		ax.set_xlabel('Datetime')
		ax.set_ylabel('State')
		ax.set_title('Sleep states')
		
		handles = list(legend_handles.values())
		labels = list(legend_handles.keys())

		# Display the plot
		plt.legend(handles= handles, labels = labels, loc = "upper right")
		plt.show()
		




M = Devices_OAuth2flow(client_id = 'e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc', 
		       costumer_secret = 'c2b3bd8f8fa210533aa3e7ef54abd4654d2a44cfe4f33d9f3aff63b4ce0943c4',
		       callback_uri = 'http://localhost:5000')
M.get_user_credentials()
M.devices_info()
#M.intra_activitydata()
M.activity_data()
M.sleep()
#M.deactivate_raw_data()
#M.activate_raw_data()
