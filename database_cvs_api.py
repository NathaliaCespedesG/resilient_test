import pandas as pd
import os
import requests
#from database_backend.api.models import User

# POST THE EXISTING USERS TO THE DATABASE
def import_users_from_csv(users_path):
    
    #User = models_api.User()
        
    if os.path.exists(users_path):
        # Open the CSV file in read mode
        with open(users_path, 'r', newline='') as csv_file:
            df = pd.read_csv(users_path, header = 0, delimiter=';')
           


    # Define values for the new columns
    
    role = 'participant'
    password_hash = 'NONEYET'

    custom_headers = ['username', 'role', 'password_hash']

    # Add new columns with constum headers
    df = pd.DataFrame(df, columns=['Id', 'Date of Registration'] + custom_headers)
    df[custom_headers[0]] = df['Id'].values
    df[custom_headers[1]] = role
    df[custom_headers[2]] = password_hash

    columns_to_remove = ['Id', 'Date of Registration']
    df = df.drop(columns=columns_to_remove)

    data = df.to_dict(orient='records')

    for i in range (len(data)):
        # Make POST request to Django server
        url = 'http://127.0.0.1:8000/api/users/'
        response = requests.post(url, json=data[i])
        
        if response.status_code == 200:
            print('Data updated successfully')
        else:
            print('Failed to update data:', response.text)

# GET ALL THE USERS

def get_users():
    url = 'http://127.0.0.1:8000/api/users'
    response = requests.get(url)
    # Checking the status code of the response
    if response.status_code == 200:
        # Successful response
        print('GET request successful')
        # Accessing the response data
        data = response.json()  # Assuming the response is JSON data
        #print(data)
    else:
        # Unsuccessful response
        print('GET request failed:', response.status_code)
        
    # Create a new dictionary to store id and username
    id_username_dict = {}
    # Iterate through each user in the 'users' list
    for user in data['users']:
        # Add id and username to the new dictionary
        id_username_dict[user['id']] = user['username']
        #print(id_username_dict)
    
    change_created_at(users_path ='/home/nathalia/Withings_ScanWatch/Withings_ScanWatch/db/Users.csv',
                      user_dict= id_username_dict)

#UPLOAD DEVICES FOR EACH USER
    



    





#CHANGE A VALUE IN THE USERS TABLE
            
def change_created_at(users_path, user_dict):

    fit_dict = {}
    result_dict = {}
     
    if os.path.exists(users_path):
        # Open the CSV file in read mode
        with open(users_path, 'r', newline='') as csv_file:
            df = pd.read_csv(users_path, header = 0, delimiter=';')
            fit_dict = df.to_dict(orient='records')
            fit_dict = {entry['Id']: entry[' Date of Registration'] for entry in fit_dict}
    
    #print(fit_dict)

    
    # Iterate over the items in fit_dict
    
    for key, value in fit_dict.items():
        # Check if the key in fit_dict is a key in user_dict
        if key in user_dict.values():
            # Find the corresponding key in user_dict
            user_key = next(k for k, v in user_dict.items() if v == key)
            # Add the key-value pair to the result_dict
            result_dict[user_key] = value
            url = 'http://127.0.0.1:8000/api/user/' + user_key + '/'
            data = {'created_at': value}
            response = requests.patch(url, json = data)
            # Checking the status code of the response
            if response.status_code == 200:
                # Successful response
                print('PATCH request successful')
                # Accessing the response data
                data = response.json()  # Assuming the response is JSON data
                print(data)
            else:
                # Unsuccessful response
                print('PATCH request failed:', response.status_code)

    

    

                
    


    

    
            

   
    

            
  



            
   
path = '/home/nathalia/Withings_ScanWatch/Withings_ScanWatch/db/Users.csv'
import_users_from_csv(path)
#get_users()
#change_created_at(path)
    

        
      