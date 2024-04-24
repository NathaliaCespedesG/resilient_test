import pandas as pd
import os
import requests
import math
from datetime import datetime, timezone
#from database_backend.api.models import User


class Database_API(object):
    
    def __init__(self):
        pass
    
    def register(self, user = None, role = None, password_hash = None):

        url = 'http://127.0.0.1:8000/api/users/'

        data = {
                "username": user,
                "role": role,
                "password_hash": password_hash
                }
        
        response = requests.post(url, json = data)
        if response.status_code == 400:
            print('User already in the database')

    def get_users(self):
        
        url = 'http://127.0.0.1:8000/api/users'
        response = requests.get(url)
        
        # Checking the status code of the response
        if response.status_code == 200:
            # Successful response
            print('GET request successful')
            # Accessing the response data
            self.user_data = response.json()  # Assuming the response is JSON data
            #print(data)
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)

        # Filter by participant and study participant
        self.filtered_data = [{entry['id']: entry['username']} for entry in self.user_data['users'] if entry['role'] in ['study-participant', 'study-partner-participant']]
        
        return(self.filtered_data)
    
    def get_unique_id(self, id_user = None):
        
        url = 'http://127.0.0.1:8000/api/users/?username='+ str(id_user)
        response = requests.get(url)
        
        # Checking the status code of the response
        if response.status_code == 200:
            # Successful response
            print('GET request successful')
            # Accessing the response data
            unique_id = response.json()  # Assuming the response is JSON data
            #print(data)
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)
        
        return(unique_id)

    def upload_device_info(self, user = None, dict = None):
        url= 'http://127.0.0.1:8000/api/devices/'

        for j in range(len(dict)):
            
            data ={
                "user": user,
                "device_hash": dict[j]['Hash_deviceid'],
                "device_type": {'Activity Tracker': 'scan_watch', 'Sleep Monitor': 'sleep_mat','Scale':'scale'}.get(dict[j]['Device'], 'default_value'),
                "mac_address": dict[j]['MAC_address'],
                "is_active": True
                }
            #print(data)
            response = requests.post(url, json=data)
            print(response.status_code)


    def get_device_info(self, user = None):
        url = 'http://127.0.0.1:8000/api/devices/' + '?username=' + user
        response = requests.get(url)
        # Checking the status code of the response
        if response.status_code == 200:
                print('GET request successful')
                # Accessing the response data
                self.device_data = response.json()  # Assuming the response is JSON data
                #print(self.device_data)
                devices = self.organized_dict(self.device_data)
                self.devices_dict[user] = devices
                
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)






                


            

			
			
