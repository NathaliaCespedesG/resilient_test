import time
import os
import datetime

#Object to manage all the user's data

class DatabaseManager(object):

	def __init__(self,ProjectHandler = None, UserStatus = None):

		# Loading User Status

		self.UserStatus = UserStatus

		self.PH = ProjectHandler


		



	def load_Scale(self, data = None, time = None):

		#Loading data
		self.ScaleFile = open(self.scale_name, 'a')
		data = str(data) + ";" + str(time) + "\n"
		self.ScaleFile.write(data)
		self.ScaleFile.close()

	def load_ScanWatch(self, data = None, time = None):

		#Loading data
		self.ScanWatchfile = open(self.scanwatch_name, 'a')
		data = str(data) + ";" + str(time) + "\n"
		self.ScanWatchfile.write(data)
		self.ScanWatchfile.close()

	def load_SleepMat(self, data = None, time = None):

		#Loading data
		self.SleepMatFile = open(self.sleepmat_name, 'a')
		data = str(data) + ";" + str(time) + "\n"
		self.SleepMatFile.write(data)
		self.SleepMatFile.close()


	def load_SensorInfo(self, sensor = None, hash_deviceid = None, MAC_address = None):
		
		self.DevicesFile = open(self.devices_info, 'a')
		data = str(sensor)+ ";" + str(hash_deviceid) + ";" + str(MAC_address) + "\n"
		self.DevicesFile.write(data)
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
		self.DevicesFile.write("Device; Hash_deviceid; MAC_address")

		#Headers on each files

		self.ScaleFile.write("ID;Date ;Weight ;Muscle mass ;Bone mass ; Fat mass; Fat free mass; Fat ratio\n")
		self.ScanWatchfile.write("ID;Date ;HR ;Steps ;Distance ;Calories ; Intensity\n")
		self.SleepMatFile.write("ID; Date ;HR; Sleep Duration; Sleep State Duration; Awake; Light; Deep ;REM ;Sleep wakeup")

		#Closing files

		self.ScaleFile.close()
		self.ScanWatchfile.close()
		self.SleepMatFile.close()

	def finish_datastorage(self):

		#Closing files

		self.ScaleFile.close()
		self.ScanWatchfile.close()
		self.SleepMatFile.close()

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





