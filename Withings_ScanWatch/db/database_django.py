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
    
    def register(self, user = None, role = None, password_hash = None, credential_path = None,
                scale_device_id = None, scanwatch_device_id = None, sleepmat_device_id = None):

        url = 'http://127.0.0.1:8000/api/users/'
        data = {
                "username": user,
                "role": role,
                "password_hash": password_hash,
                "withings_credentials_path": credential_path
                }
        print(data)
        
        response = requests.post(url, json = data)
        print('HIII')
        if response.status_code == 400:
            print('Not working')

    def get_users(self):
        
        url = 'http://127.0.0.1:8000/api/users'
        response = requests.get(url)
        
        # Checking the status code of the response
        if response.status_code == 200:
            # Successful response
            print('GET request successful')
            # Accessing the response data
            self.user_data = response.json()  # Assuming the response is JSON data
            print(self.user_data)
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
    
    #PATCH users table
    def update_devices_in_user(self, user_uid = None, scale_id = None, scanwatch_id = None, sleepmat_id = None):
        url= 'http://127.0.0.1:8000/api/user/' + user_uid +'/'
        print(scale_id)
        data = {
             "scale_device": scale_id,
             "scanwatch_device":scanwatch_id,
             "sleepmat_device": sleepmat_id
        }
        response = requests.patch(url,json=data)
        if response.status_code == 200:
             print("PATCH request successful")
        else:
             print(f"PATCH request failed with status code {response.status_code}")


    def upload_device_info(self, dict = None):
        url= 'http://127.0.0.1:8000/api/devices/'
        print('****************************')
        print(dict)
    

        for j in range(len(dict)):
            
            data ={
                "device_hash": dict[j]['Hash_deviceid'],
                "device_type": {'Activity Tracker': 'scan_watch', 'Sleep Monitor': 'sleep_mat','Scale':'scale'}.get(dict[j]['Device'], 'default_value'),
                "mac_address": dict[j]['MAC_address'],
                "is_active": True
                }
            #print(data)
            response = requests.post(url, json=data)
            #print(response)


    def get_device_info(self, device_hash = None):
        url = 'http://127.0.0.1:8000/api/devices/' + '?device_hash=' + device_hash
        response = requests.get(url)
        self.devices_dict = {}
        # Checking the status code of the response
        if response.status_code == 200:
                print('GET request successful')
                # Accessing the response data
                data = response.json()  # Assuming the response is JSON data
                print(data)
                
        else:
            # Unsuccessful response
            print('GET request failed:', response.status_code)

        extracted_id = {device['device_type']: device['id'] for device in data['devices']}
        return(extracted_id)
    
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
        filtered_data = [{'date_heart_rate': item['date_heart_rate'], 
                          'heart_rate': item['heart_rate']} for item in scanwatch_intra_dict["scanwatches_intraactivity"] if start_date <= item['date_heart_rate'] <= end_date]

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
                          'out_of_bed_count':item['out_of_bed_count'],
                          'start_date': item['start_date'],
                          'end_date': item['end_date']
                          } for item in sleep_summary_dict["sleepmats_summary"] if start_date <= arrow.get(item['date']).datetime <= end_date]

        
        return(filtered_data)
    
    def get_sleep_intra_activity_data(self, user = None, start_date = None, end_date = None):
        
        url = 'http://127.0.0.1:8000/api/sleepmats/intraactivity/' + '?username=' + user
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

        
        # Filter data based on start_date and end_date
        filtered_data = [{'start_date': item['start_date'],
                          'end_date': item['end_date'],
                          'sleep_state': item['sleep_state'],
                          'date_heart_rate': item['date_heart_rate'],
                          'heart_rate': item['heart_rate'],
                          'date_respiration_rate': item['date_respiration_rate'],
                          'respiration_rate': item['respiration_rate'],
                          'date_snoring': item['date_snoring'],
                          'snoring': item['snoring'],
                          'date_sdnn_1': item['date_sdnn_1'],
                          'sdnn_1': item['sdnn_1'],
                          'device': item['device'],
                          } for item in sleep_intra_day_dict["sleepmats_intraactivity"] if start_date <= item['date_heart_rate']<= end_date]

        
        print(filtered_data)
        #print(hola)
        return(filtered_data)




        
    












                


            

			
			
