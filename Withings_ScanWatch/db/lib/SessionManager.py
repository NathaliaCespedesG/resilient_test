import time
import os
import datetime
import pandas as pd
import numpy as np

#Object to manage all the user's data

class DatabaseManager(object):

	def __init__(self,ProjectHandler = None, UserStatus = None):

		# Loading User Status

		self.UserStatus = UserStatus

		self.PH = ProjectHandler

		self.date = datetime.datetime.now()


	def load_Scale(self, time = None, weight = None, muscle_mass = None, bone_mass = None, fat_mass = None):


		#Loading data
		self.ScaleFile = open(self.scale_name, 'a')
		for i in range (len(time)):
			self.df_scale  = self.df_scale.append({'date':time[i],'Weight': weight[i], 'Muscle mass': muscle_mass[i], 'Bone mass': bone_mass[i] , 'Fat mass Weight': fat_mass[i]}, ignore_index=True)
		self.df_scale.to_csv(self.scale_name, index = False )

		self.ScaleFile.close()

	def load_ScanWatch(self, time = None, hr = None, calories = None, steps = None):

		#Loading data
		self.ScanWatchfile = open(self.scanwatch_name, 'a')
		for i in range (len(time)):
			self.df_scanwatch = self.df_scanwatch.append({'date': time[i], 'HR_Average':hr[i],'Calories': calories[i], 'Steps': steps[i]}, ignore_index=True)
		self.df_scanwatch.to_csv(self.scanwatch_name, index = False )

		self.ScanWatchfile.close()

	def load_SleepMat(self, time = None, bd = None, dsd = None, dts = None, dtw = None, hr = None, lsd = None, rsd = None, rr = None, ss = None,wpc = None, wpd = None):

		#Loading data
		self.SleepMatFile = open(self.sleepmat_name, 'a')

		for i in range (len(time)):
			self.df_sleepsummary = self.df_sleepsummary.append({'date': time[i], 'Breathing disturbances': bd[i], 'Deep sleep duration': dsd[i], 'Duration to sleep': dts[i] , 'Duration to wakeup': dtw[i],
								'HR average': hr[i], 'Light sleep duration': lsd[i], 'Rem sleep duration': rsd[i], 'RR average': rr[i], 'Sleep score': ss[i], 'Wake up count': wpc[i],
								'Wake up duration': wpd[i]}, ignore_index=True)
		self.df_sleepsummary.to_csv(self.sleepmat_name, index = False )

	
		self.SleepMatFile.close()


	def load_SensorInfo(self, sensor = None, hash_deviceid = None, MAC_address = None):
		
		self.DevicesFile = open(self.devices_info, 'a')
		for i in range (len(sensor)):

			self.df_devices = self.df_devices.append({'Device': sensor[i], 'Hash_deviceid': hash_deviceid[i], 'MAC_address': MAC_address[i]}, ignore_index = True)
		
		self.df_devices.to_csv(self.devices_info, index = False )

		self.DevicesFile.close()



	def load_intra_activity(self, time = None, hr = None, time_steps = None, steps = None,  time_calories = None, calories = None):

		self.ScanIntraFile = open(self.scanwatch_intraday, 'a')

		max_size = max(len(time), len(time_steps), len(time_calories))

		if len(time) < max_size:

			time = np.append(time, [np.nan] * (max_size - len(time)))
			hr = np.append(hr, [np.nan] * (max_size - len(hr)))

		# Fill time_steps and steps with NaN until they reach max_size

		if len(time_steps) < max_size:

			time_steps = np.append(time_steps, [np.nan] * (max_size - len(time_steps)))
			steps = np.append(steps, [np.nan] * (max_size - len(steps)))

		# Fill time_calories and calories with NaN until they reach max_size

		if len(time_calories) < max_size:
			time_calories = np.append(time_calories, [np.nan] * (max_size - len(time_calories)))
			calories = np.append(calories, [np.nan] * (max_size - len(calories)))


		for i in range(max_size):

			self.df_scawatch_intra = self.df_scawatch_intra.append({'date HR': time[i], 'Heart Rate': hr[i], 'date Steps': time_steps[i], 'Steps': steps[i], 'date Calories': time_calories[i] , 'Calories': calories[i]},ignore_index = True)

		self.df_scawatch_intra.to_csv(self.scanwatch_intraday, index = False)
		self.ScanIntraFile.close()

	def load_intra_sleep(self, start_date = None, end_date = None, ss = None, hr = None, hr_date = None, rr = None, rr_date = None, snoring = None, snoring_date = None, sdnn_1 = None, sdnn_1_date = None):

		max_size = max(len(start_date), len(hr_date))
		self.SleepIntraFile = open(self.sleepmat_intraday, 'a')
		#print(hr)

		if len(start_date) < max_size:

			start_date = np.append(start_date, [np.nan] * (max_size - len(start_date)))
			end_date = np.append(end_date, [np.nan] * (max_size - len(end_date)))
			ss = np.append(ss, [np.nan] * (max_size - len(ss)))

		for i in range(max_size):
			#print('Here intra')

			self.df_sleep_intra  = self.df_sleep_intra.append({'startdate': start_date[i], 'enddate': end_date[i], 'Sleep state':ss[i], 'Heart Rate date': hr_date[i], 'Heart Rate': hr[i] ,  'Respiration rate date': rr_date[i],
			 													'Respiration rate': rr[i] , 'Snoring date': snoring_date[i], 'Snoring': snoring[i], 'sdnn_1 date': sdnn_1_date[i], 'sdnn_1': sdnn_1[i]} ,ignore_index = True)


		self.df_sleep_intra.to_csv(self.sleepmat_intraday, index = False)
		self.SleepIntraFile.close()




	def set_User(self, US):

		#User status
		self.UserStatus = US


	def get_path(self):

		return(self.user_folder)


	def create_session(self):

		#Create folders for each user

		self.user_folder_wd = self.PH + "/" +"General" + "/" + str(self.UserStatus['id'])

		self.user_folder = self.PH + "/" +"General" + "/" + str(self.UserStatus['id']) +"/"+ str(self.date.year) +"-"+ str(self.date.month)+"-"+ str(self.date.day)
	

		if not os.path.exists(self.user_folder):
			os.makedirs(self.user_folder)


		#Create sensors file

		self.scale_name = self.user_folder + "/Scale.csv"
		self.scanwatch_name = self.user_folder + "/ScanWatch_summary.csv"
		self.sleepmat_name = self.user_folder + "/SleepMat_summary.csv"
		self.devices_info = self.user_folder_wd+ "/Devices.csv"

		#Create sensors file for higher granularity

		self.scanwatch_intraday = self.user_folder + "/ScanWatch_intra_activity.csv"
		self.sleepmat_intraday = self.user_folder + "/Sleepmat_intra_activity.csv"
		

		#Open the files to save the data
		self.ScaleFile = open(self.scale_name, 'w+')
		self.ScanWatchfile = open(self.scanwatch_name, 'w+')
		self.SleepMatFile = open(self.sleepmat_name, "w+")
		self.DevicesFile = open(self.devices_info, "w+")
		self.ScanIntraFile = open(self.scanwatch_intraday, "w+")
		self.SleepIntraFile = open(self.sleepmat_intraday, "w+")

		#Headers on devices files

		self.df_devices = pd.DataFrame({'Device': [], 'Hash_deviceid': [], 'MAC_address': []} )
		self.df_devices.to_csv(self.devices_info, index = False )

		#Headers on each files

		self.df_scanwatch = pd.DataFrame({'date': [], 'HR_Average': [], 'Calories': [], 'Steps': []} )
		self.df_scanwatch.to_csv(self.scanwatch_name, index = False )


		self.df_scale = pd.DataFrame({'date': [], 'Weight': [], 'Muscle mass': [], 'Bone mass': [] , 'Fat mass Weight': [] } )
		self.df_scale.to_csv(self.scale_name, index = False )

		self.df_sleepsummary = pd.DataFrame({'date': [], 'Breathing disturbances': [], 'Deep sleep duration': [], 'Duration to sleep': [] , 'Duration to wakeup': [],
								'HR average': [], 'Light sleep duration': [], 'Rem sleep duration': [], 'RR average': [], 'Sleep score': [], 'Wake up count': [],
								 'Wake up duration': []} )
		self.df_sleepsummary.to_csv(self.sleepmat_name, index = False )


		self.df_scawatch_intra = pd.DataFrame({'date HR': [], 'Heart Rate': [], 'date Steps':[], 'Steps': [], 'date Calories': [] , 'Calories': []})
		self.df_scawatch_intra.to_csv(self.scanwatch_intraday, index = False)

		self.df_hr = pd.DataFrame({'date HR': [], 'Heart Rate': []})
		self.df_steps = pd.DataFrame({'date Steps': [], 'Steps': []})
		self.df_calories = pd.DataFrame({'date Calories': [], 'Calories': []})
		#self.df_scanwatch_intra.to_csv(self.scanwatch_intraday, index = False )

		self.df_sleep_intra =  pd.DataFrame({'startdate':[], 'enddate': [], 'Sleep state':[], 'Heart Rate date': [], 'Heart Rate': [] ,  'Respiration rate date': [],
			 												'Respiration rate': [] , 'Snoring date': [], 'Snoring': [], 'sdnn_1 date': [], 'sdnn_1': []})
		self.df_sleep_intra.to_csv(self.sleepmat_intraday, index = False)

		#Closing files

		self.ScaleFile.close()
		self.ScanWatchfile.close()
		self.SleepMatFile.close()
		self.ScanIntraFile.close()
		self.SleepIntraFile.close()


	def finish_datastorage(self):

		#Closing files

		self.ScaleFile.close()
		self.ScanWatchfile.close()
		self.SleepMatFile.close()
		self.TestFile.close()
		self.ScanIntraFile.close()
		self.SleepIntraFile.close()

	def set_user(self, p):

		self.user = p

	def register_user(self, id_user = 'nd'):

		print('Here in register user from SM')

		self.user = {"id" : id_user}
		self.save_user()
		self.set_User(US = self.UserStatus)
		self.create_session()
		return self.UserStatus

	def save_user(self):

		print('In save_user')

		#Check the user in the database

		self.UserStatus = self.check_user()
		print('UserStatus', self.UserStatus)

		path = self.PH

		if not self.UserStatus['registered']:

			print('Here not registered')

			#path = self.PH

			if os.path.exists(path + "/Users.csv"):

				f = open(path + "/Users.csv", 'a')

				#save new user information
				#rint()

				f.write(self.user['id']+";"+(str(self.date.year) +"-"+ str(self.date.month)+"-"+ str(self.date.day))+'\n'
                    )

		else:
			print('registered')

			#f = open(path + "/Users.csv", 'w+')
			#f.write("Id; Date of Registration\n")
			#f.close()

			#f = open(path + "/Users.csv", 'a')
			#save new user information
			#f.write(self.user['id']          +";" +'\n')
			#close the file
			#f.close()


	def check_user(self):

		print('Checking User Status')

		path = self.PH

		if os.path.exists(path + "/Users.csv"):

			print('Exists')

			f = open(path + "/Users.csv", 'r')
			lines = f.readlines()
			f.close()
			users = lines[1:]
			print(users)
			#check patient lists
			for p in users:
				pl = p.split(";")
				if pl[0] == self.user['id']:
					print("User Already in the database")
					return {"registered" : True,"id" : self.user['id']}

			return{"registered" : False, "id" : self.user['id']}

		else:

			print('No Exists')

			f = open(path + "/Users.csv", 'w+')
			f.write("Id; Date of Registration\n")
			f.close()
			return {"registered" : False, "id" : self.user['id']}





