#This is the code to run all the participant reports
import sys 
import os 
from os import path 
import pandas as pd
import Devices_OAuth2flow as reports
import shutil

class Resilient(object):

    def __init__(self):

        # Types of generation

        gen_type = input('Please indicate  the type of report you want to generate, all - one - create: ')

        self.users_path()

        print(gen_type)

        '''

        if gen_type == 'all':
            
            self.run_all_participants()

        elif gen_type == 'create' :

            self.create_participant()
        '''

    def users_path(self):

        #Current path for the Main class
        self.current_path = os.getcwd()
        #User's file path
        users = 'db/Users.csv'

        self.users_path = path.abspath(path.join(self.current_path, users))
        # Check if the file exists
        if os.path.exists(self.users_path):
            # Open the CSV file in read mode
            with open(self.users_path, 'r', newline='') as csv_file:
                df = pd.read_csv(self.users_path, header = 0, delimiter=';')
                if "Id" in df.columns:
                    self.id_available = df['Id'].values
                    #print(id_available)

                else:
                    print('The id colum does not exists ')
        else:
            self.id_available = None
            print(f"The file '{self.users_path}' does not exist.")

    

    def run_all_participants(self):

        
        if self.id_available is not None:
            print(self.id_available[1])
            
            total_participants = len(self.id_available)
            print(total_participants)


            for i in range (total_participants):

                id_report = self.id_available[i]
                
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
        
        reports_resilient = reports.Devices_OAuth2flow(client_id = 'e64cb563bf44122144cd0702b02f69ad50d21aba0eb50ca443f69db5673ca2cc', 
		                            costumer_secret = 'c2b3bd8f8fa210533aa3e7ef54abd4654d2a44cfe4f33d9f3aff63b4ce0943c4',
		                            callback_uri = 'https://resilient.ukdri.care/',
		                            report_type = 0,
			                        generation_type = 'create',
                                    id_participant = None)

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

    
    def merge_pdf(self):
        pass

    def create_folder_reports(self):

        folder_path = self.current_path + 'reports'
        general = 'db/General'
        #source_folder = path.abspath(path.join(self.current_path,

        try:
            os.mkdir(folder_path)
            print('Folder created correctly')
        
        except OSError as error:
            print('Failed to create folder in the path')

        
        for i in range (len(self.id_available)):
            #General database path for the users folders
            new_path = path.abspath(path.join(self.current_path, general, self.id_available[i]))
            # Latest directory on the file
            latest = self.latest_directory(directory_path = new_path)
            # General path + latest directory
            latest_user_directory = path.abspath(path.join(new_path, latest))
            # pdf files
            pdf_file = self.pdf_file_search(latest_user_directory)
            
            # General path + latest directory + pdf
            pdf_file_user = path.abspath(path.join(latest_user_directory, str(pdf_file[0])))

            print(pdf_file_user)


            self.copy_pdf(source_path = pdf_file_user, destination_path = folder_path)
            #source_path = os.path.join()
    
    def latest_directory(self, directory_path = None):

        directories = [d for d in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, d))]
    
        if not directories:
            
            latest_directory = None  # If there are no directories in the path, return None
    
        # Get the latest directory based on modification time
        latest_directory = max(directories, key=lambda d: os.path.getmtime(os.path.join(directory_path, d)))

        return(latest_directory)
    
    def pdf_file_search(self, directory_path = None):
        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        # Filter out PDF files
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        return pdf_files
    
    def copy_pdf(self, source_path = None, destination_path = None):
        
        try:
            shutil.copy(source_path, destination_path)
            print("PDF file copied successfully from.")
            
        except FileNotFoundError:
            print("Source file not found.")
        
        except PermissionError:
            print("Permission denied.")
            
        except Exception as e:
            print(f"Error: {e}")



        
 






        

    
    

        
a = Resilient()
a.create_folder_reports()