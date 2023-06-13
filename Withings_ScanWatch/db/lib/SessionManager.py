import time
import os
import datetime
import pandas as pd

#Object to manage all the user's data

class DatabaseManager(object):

	def __init__(self,ProjectHandler = None, UserStatus = None):

		# Loading User Status

		self.UserStatus = UserStatus

		self.PH = ProjectHandler


		



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


	def set_User(self, US):

		#User status
		self.UserStatus = US




	def create_session(self):

		#Create folders for each user

		user_folder = self.PH + "/" +"General" + "/" + str(self.UserStatus['id'])

		if not os.path.exists(user_folder):
			os.makedirs(user_folder)


		#Create sensors file

		self.scale_name = user_folder + "/Scale.csv"
		self.scanwatch_name = user_folder + "/ScanWatch.csv"
		self.sleepmat_name = user_folder + "/SleepMat.csv"
		self.devices_info = user_folder + "/Devices.csv"

		#Open the files to save the data
		self.ScaleFile = open(self.scale_name, 'w+')
		self.ScanWatchfile = open(self.scanwatch_name, 'w+')
		self.SleepMatFile = open(self.sleepmat_name, "w+")
		self.DevicesFile = open(self.devices_info, "w+")

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



		#Closing files

		self.ScaleFile.close()
		self.ScanWatchfile.close()
		self.SleepMatFile.close()

	def finish_datastorage(self):

		#Closing files

		self.ScaleFile.close()
		self.ScanWatchfile.close()
		self.SleepMatFile.close()
		self.TestFile.close()

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

				f.write(self.user['id']+";"+'\n'
                    )

		else:
			print('registered')

			f = open(path + "/Users.csv", 'w+')
			f.write("Id;\n")
			f.close()

			f = open(path + "/Users.csv", 'a')
			#save new user information
			f.write(self.user['id']          +";" +'\n'
					)
			#close the file
			f.close()
		
		


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
			f.write("Id;\n")
			f.close()
			return {"registered" : False, "id" : self.user['id']}





