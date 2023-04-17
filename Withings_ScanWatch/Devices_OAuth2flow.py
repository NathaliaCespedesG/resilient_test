from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from withings_api import WithingsAuth, WithingsApi, AuthScope
from withings_api.common import get_measure_value, MeasureType, CredentialsType, MeasureGetActivityResponse
import arrow
import time

#To save users credential and update refresh the token

import argparse
import os
from os import path
import pickle
from typing import cast
from urllib import parse
from typing_extensions import Final



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
			self.api = WithingsApi(self.load_credentials())
			try:
				self.api.user_get_device()
			except MissingTokenError:
				os.remove(self.CREDENTIALS_FILE)
				print("Credentials in file are expired. Re-starting auth procedure...")

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
			self.api = WithingsApi(self.load_credentials())
                
                orig_access_token = api.get_credentials().access_token
                print("Refreshing token...")
                api.refresh_token()
                #assert orig_access_token != api.get_credentials().access_token

			
	


	def devices_info(self):

		# This function generates the device information. For instance, the hash_deviceid,
		# battery levels, serial number, device_id, among others. Some of this parameters
		# are used in other services to activate functions.

		devices = self.api.user_get_device()
		#print('Devices',devices)
		self.hash_deviceid = devices['devices']
		self.hash_deviceid = self.hash_deviceid[0]['hash_deviceid']


	def create_nonce(self):

		# This function generates the nonce. The nonce is a signature used
		# to sign requests and it is used by some Withings services.

		signature = self.api.get_signature()
		self.nonce = signature['body']['nonce']
		print('nonce', self.nonce)

	def activity_data(self, type_activity = None): 

		# This function returns the activity data. Please refer
		# to the withings API documentation to see what type of data
		# you can get from this service.

		activity_data = {}

		self.meas_activity  =  self.api.measure_get_activity(startdateymd = arrow.utcnow().shift(days=-10), enddateymd = arrow.utcnow())
		#print('ACTIVITY', self.meas_activity)
		print('Meas activity', self.meas_activity.activities[0].hr_average)
		activity_data['heart_rate'] = [x.hr_average for x in self.meas_activity.activities]
		activity_data['date'] = [arrow.get(x.date) for x in self.meas_activity.activities]
		print('This is the HR', activity_data)
		print(type(self.meas_activity.activities[:]))


		#if type_activity == 'HR':
			#return('Heart_rate', self.meas_activity.activities[:].hr_average)

	def intra_activitydata(self):
		
		self.meas_intraactivity = api.measure_get_intraactivity(startdate = arrow.utcnow().shift(hours=-24), enddate  = arrow.utcnow())
		print('Meas Intraactivity', meas_intraactivity)
		print(type(meas_intraactivity))
		#self.meas_intraactivity.

	def raw_data_acquisition(self):

		get_raw = self.api.get_raw_data(hash_deviceid = self.hash_deviceid, rawdata_type = 1, startdate = arrow.utcnow().shift(days=-20), enddate = arrow.utcnow().shift(days=-1))
		#print(get_raw)









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




	



M = Devices_OAuth2flow(client_id = 'e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc', 
		       costumer_secret = 'c2b3bd8f8fa210533aa3e7ef54abd4654d2a44cfe4f33d9f3aff63b4ce0943c4',
		       callback_uri = 'http://localhost:5000')
M.get_user_credentials()
M.devices_info()
hr = M.activity_data(type_activity = 'HR' )
print(hr)
#M.raw_data_acquisition()
