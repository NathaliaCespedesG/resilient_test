#This is the code to run all the participant reports
import sys 
import os 
from os import path 
import pandas as pd
import Devices_OAuth2flow as reports

class Resilient(object):

    def __init__(self):

        # Types of generation

        gen_type = input('Please indicate  the type of report you want to generate, all - one - create: ')

        print(gen_type)

        if gen_type == 'all':
            
            self.run_all_participants()

        elif gen_type == 'one':

            self.run_one_participant()

        elif gen_type == 'create' :

            self.create_participant()
    

    def run_all_participants(self):

        #Current path for the Main class
        current_path = os.getcwd()
        #User's file path
        users = 'db/Users.csv'

        self.users_path = path.abspath(path.join(current_path, users))
        # Check if the file exists
        if os.path.exists(self.users_path):
            # Open the CSV file in read mode
            with open(self.users_path, 'r', newline='') as csv_file:
                df = pd.read_csv(self.users_path, header = 0, delimiter=';')
                if "Id" in df.columns:
                    id_available = df['Id'].values
                    #print(id_available)

                else:
                    print('The id colum does not exists ')
        else:
            id_available = None
            print(f"The file '{self.users_path}' does not exist.")


        
        if id_available is not None:
            print(id_available[1])
            
            total_participants = len(id_available)
            print(total_participants)


            for i in range (total_participants):

                id_report = id_available[i]
                print(type(id_report))

                print(id_available[i])
                
                reports_resilient = reports.Devices_OAuth2flow(client_id = 'e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc', 
		                            costumer_secret = 'c2b3bd8f8fa210533aa3e7ef54abd4654d2a44cfe4f33d9f3aff63b4ce0943c4',
		                            callback_uri = 'https://resilient.ukdri.care/',
		                            report_type = 0,
			                        generation_type = 'all',
                                    id_participant = id_report)

                reports_resilient.get_user_credentials()
                reports_resilient.devices_info()
                reports_resilient.scale_data()
                reports_resilient.sleep()
                reports_resilient.sleep_daily()
                reports_resilient.activity_data_watch()
                reports_resilient.plot_creator()
                reports_resilient.doc_generation()
                reports_resilient.remove_images()
                reports_resilient.usage_levels()

            

    
    def create_participant(self):

        pass
    
    def run_one_participant(self):

        pass

        
a = Resilient()