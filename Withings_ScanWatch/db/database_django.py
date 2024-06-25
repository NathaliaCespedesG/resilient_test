import pandas as pd
import os
import requests
import math
from datetime import datetime, timezone
import arrow
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
        self.devices_dict = {}
        # Checking the status code of the response
        if response.status_code == 200:
                print('GET request successful')
                # Accessing the response data
                self.device_data = response.json()  # Assuming the response is JSON data
                #print(self.device_data)
                devices = self.organized_dict(self.device_data)
                
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)
        
        return(devices)
    
    def organized_dict(self, original_dict):
        converted_dict = {}
        for device in original_dict['devices']:
            user = device['user']
            device_type = device['device_type']
            #print(device_type)
            device_id = device['id']
            if user not in converted_dict:
                converted_dict[user] = {}
            
            converted_dict[user][device_type] = device_id
                
                
        return(converted_dict)
    
    def upload_scanwatch_summary_data(self):

        url = 'http://127.0.0.1:8000/api/scanwatches/summary/'
     
        if watch_id is not None:

            for j in range(len(dict)):
                date_s = dict[j]['date'][:-6]
                date_s = datetime.strptime(date_s, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')

                # Convert 'nan' values to None
                average_heart_rate = 0 if math.isnan(float(dict[j]['HR_Average'])) else float(dict[j]['HR_Average']) 
                calories = 0 if math.isnan(float(dict[j]['Calories'])) else float(dict[j]['Calories'])
                steps = 0 if math.isnan(float(dict[j]['Steps'])) else float(dict[j]['Steps'])
        
                data ={
                    "device": watch_id,
                    "date": date_s,
                    "average_heart_rate": average_heart_rate,
                    "calories": calories,
                    "steps": steps
                    }
                
                print(data)
                response = requests.post(url, json=data)


    def get_scanwatch_summary_data(self,user = None, start_date = None, end_date = None):
        
        url = 'http://127.0.0.1:8000/api/scanwatches/summary/' + '?username=' + user
        
        response = requests.get(url)
        scanwatch_dict = {}
        # Checking the status code of the response
        if response.status_code == 200:
                print('GET request successful')
                # Accessing the response data
                scanwatch_dict = response.json()  # Assuming the response is JSON data
                #print(scanwatch_dict)
                
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)

        # Filter data based on start_date and end_date
        filtered_data = {'scanwatches_summary': [item for item in scanwatch_dict['scanwatches_summary'] if end_date <= arrow.get(item['date']).datetime <= start_date]}
        
        return(filtered_data)
    
    def get_scanwatch_intra_activity_data(self, user = None, start_date = None, end_date = None):

        url = 'http://127.0.0.1:8000/api/scanwatches/intra_activity/' + '?username=' + user
        response = requests.get(url)
        scanwatch_intra_dict = {}
        # Checking the status code of the response
        if response.status_code == 200:
                print('GET request successful')
                # Accessing the response data
                scanwatch_intra_dict = response.json()  # Assuming the response is JSON data
                #print(scanwatch_dict)
                
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)

        # Filter data based on start_date and end_date
        filtered_data = [{'date_heart_rate': item['date_heart_rate'], 'heart_rate': item['heart_rate']} for item in scanwatch_intra_dict["scanwatches_intraactivity"] if start_date <= item['date_heart_rate'] <= end_date]

        #print(filtered_data)
        
        return(filtered_data)
    
    def get_sleep_summary_data(self, user = None, start_date = None, end_date = None):

        url = 'http://127.0.0.1:8000/api/sleepmats/summary/' + '?username=' + user
        response = requests.get(url)
        sleep_summary_dict = {}
        # Checking the status code of the response
        if response.status_code == 200:
                print('GET request successful')
                # Accessing the response data
                sleep_summary_dict = response.json()  # Assuming the response is JSON data
                
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)

        # Filter data based on start_date and end_date
        filtered_data = [{'date': item['date'],
                          'breathing_disturbances': item['breathing_disturbances'],
                          'deep_sleep_duration': item['deep_sleep_duration'],
                          'duration_to_sleep': item['duration_to_sleep'],
                          'duration_to_wakeup': item['duration_to_wakeup'],
                          'average_heart_rate': item['average_heart_rate'],
                          'light_sleep_duration': item['light_sleep_duration'],
                          'rem_sleep_duration': item['rem_sleep_duration'],
                          'average_rr': item['average_rr'],
                          'sleep_score': item['sleep_score'],
                          'wakeup_count': item['wakeup_count'],
                          'wakeup_duration': item['wakeup_duration'],
                          'total_sleep_time': item['total_sleep_time'],
                          'total_time_in_bed': item['total_time_in_bed'],
                          'awake_in_bed': item['awake_in_bed'],
                          'apnea':item['apnea'],
                          'out_of_bed_count':item['out_of_bed_count']

                          } for item in sleep_summary_dict["sleepmats_summary"] if start_date <= arrow.get(item['date']).datetime <= end_date]

        
        return(filtered_data)
    
    def get_sleep_intra_activity_data(self, user = None, start_date = None, end_date = None):
        
        url = 'http://127.0.0.1:8000/api/sleepmat/intraactivity/' + '?username=' + user
        response = requests.get(url)
        sleep_intra_day_dict = {}
        # Checking the status code of the response
        if response.status_code == 200:
                print('GET request successful')
                # Accessing the response data
                sleep_intra_day_dict = response.json()  # Assuming the response is JSON data
                
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)

        print(sleep_intra_day_dict)



        
    












                


            

			
			
