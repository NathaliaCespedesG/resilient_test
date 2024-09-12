#This is the code to run all the participant reports
import sys 
import os 
from os import path 
import pandas as pd
from PyPDF2 import PdfMerger
import shutil
from datetime import datetime
import numpy as np
import time

# Resources for PDF generating
import Devices_OAuth2flow as reports
import resources.PDF_usage_generation as usage_pdf

# Developer credentials
import withings_devOp_credentials as dev_credentials

# Database API
import db.database_django as database_api
import db.database as database


class Resilient(object):

    def __init__(self, report_type: None,
                user: None):


        # Types of generation

        self.db_type =  input('Please indicate  the running mode, original - test:' )

        # Database calling

        self.database_api = database_api.Database_API()
        self.database = database.General(db_type = self.db_type)

        # Report Type
        self.report_type = report_type
        self.gen_type = input('Please indicate  the type of report you want to generate, all - one - create: ')

        #Participant number if the incoming report type is one
        self.participant = user

        

        # Database from CVS files instructions
        #self.users_path()

        self.general = 'db/General'
        self.current_path = os.getcwd()
        
    def create_new_user(self, id_user = None, code = None, role = None):
        self.id_available = id_user
        #register participant - csv API
        self.database.SM.set_date_report(date = datetime.now().strftime('%Y-%m-%d'))
        self.database.register(user = self.id_available)
        # register participant - database API
        self.role = input('Please provide the role: ')
        self.password = 'NoneYet'
        self.path_cred = 'Path'
        self.database_api.register(user = self.id_available, role = self.role, password_hash = self.password, credential_path = self.path_cred)
        reports_resilient = reports.Devices_OAuth2flow(client_id = dev_credentials.client_id, 
		                            costumer_secret = dev_credentials.costumer_secret,
		                            callback_uri = dev_credentials.callback_uri,
		                            report_type = 0,
                                    id_participant = id_user,
                                    running_type = self.db_type)
        reports_resilient.save
        
        reports_resilient.get_user_credentials()
        
    def custom_sort(self,val):
        try:
            return (int(val), '')  # Return the number as primary sorting key
        except ValueError:
            # If conversion fails (for strings like '4s'), return the numeric part and original string
            numeric_part = ''.join([c for c in val if c.isdigit()])  # Extract numeric part
            return (int(numeric_part), val) 

        
            
    def individual_report_generation(self):

        users = self.current_users()
        if self.gen_type == 'all':

            self.id_available = users
            self.id_available.sort(key=self.custom_sort)
            try:
                self.run_all_participants()

                return({'status': 'success', 'path': 'withings_reports'})
        
            except Exception as e:
                # You can log the error or print it if needed
                print(f"An error occurred: {e}")
                print(hola)
                
                return({'status': 'failed', 'path': None})
        

        elif self.gen_type == 'create' :

            id_user = input('Please provide the id for the user: ')
            
            if id_user in users:
                print("Participant already in the database")
            else:
                self.id_available = id_user
                #register participant - csv API
                self.database.SM.set_date_report(date = datetime.now().strftime('%Y-%m-%d'))
                self.database.register(user = self.id_available)
                # register participant - database API
                self.role = input('Please provide the role: ')
                self.password = 'NoneYet'
                self.path_cred = 'Path'
                self.database_api.register(user = self.id_available, role = self.role, password_hash = self.password, credential_path = self.path_cred)

                self.create_participant(user = id_user)
                

        elif self.gen_type == 'one':

            self.id_available = [] 

            id_user = input('Please provide the id for the user: ')
            # when using the incoming value from web
            #id_user = self.participant    

            if id_user in users:
                try:
                    self.id_available.append(id_user)
                    self.run_all_participants()
                    return({'status': 'success', 'path':'one'})
                
                except Exception as e:
                    # You can log the error or print it if needed
                    print(f"An error occurred: {e}")
                    return({'status': 'failed', 'path': None})
            else:
                print("Participant not in the database")

    #This function uses the csv files 
    def read_users_path(self):

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
                    print(self.id_available)

                else:
                    print('The id colum does not exists ')
        else:
            self.id_available = None
            print(f"The file '{self.users_path}' does not exist.")


    def current_users(self):
        
        data = self.database_api.get_users()
        usernames = [list(item.values())[0] for item in data]

        return(usernames)


    def run_all_participants(self):
        
        if self.id_available is not None:
            print(self.id_available)
            total_participants = len(self.id_available)
            for i in range (total_participants):

                id_report = self.id_available[i]
                reports_resilient = reports.Devices_OAuth2flow(client_id = dev_credentials.client_id, 
                                    costumer_secret = dev_credentials.costumer_secret,
                                    callback_uri = dev_credentials.callback_uri,
                                    report_type = 0,
                                    id_participant = id_report,
                                    running_type = self.db_type)

                reports_resilient.get_user_credentials()
                reports_resilient.register_devices()
                reports_resilient.devices_info()
                reports_resilient.scale_data()
                time.sleep(0.5)
                reports_resilient.sleep()
                time.sleep(0.5)
                reports_resilient.sleep_daily()
                time.sleep(0.5)
                ###################################
                #reports_resilient.scale_data_v2()
                #reports_resilient.sleep_v2()
                #reports_resilient.intra_sleep_v2()
                #reports_resilient.intra_activitydata_watch_v2()
                #reports_resilient.activity_data_watch_v2()
                #reports_resilient.plot_creatorV2()
                #print(HOLA)
                ###########################################
                reports_resilient.activity_data_watch()
                reports_resilient.plot_creator()
                #print(HOLA)
                reports_resilient.db_filling()
                reports_resilient.doc_generation()
                reports_resilient.usage_levels()
                reports_resilient.remove_images()
                reports_resilient.db_cleaning()
                print(id_report)
            
    def create_participant(self, user = None):
        
        reports_resilient = reports.Devices_OAuth2flow(client_id = dev_credentials.client_id, 
		                            costumer_secret = dev_credentials.costumer_secret,
		                            callback_uri = dev_credentials.callback_uri,
		                            report_type = 0,
                                    id_participant = user,
                                    running_type = self.db_type)

        reports_resilient.get_user_credentials()
        reports_resilient.register_devices()
        reports_resilient.devices_info()
        reports_resilient.sleep()
        reports_resilient.sleep_daily()
        reports_resilient.activity_data_watch()
        reports_resilient.plot_creator()
        reports_resilient.db_filling()
        reports_resilient.doc_generation()
        reports_resilient.remove_images()
        reports_resilient.usage_levels()
        reports_resilient.db_cleaning()

    
    def sort_files(self, files):
        return sorted(files, key=lambda x: x[3]) 

    
    def merge_pdf(self):
       
        reports_folder = '/Withings_reports'
        pdfs_path = self.current_path + reports_folder
        

        pdf_files = [f for f in os.listdir(pdfs_path) if f.endswith('.pdf')]
        
        # Organize PDFs by the first three characters of their name
        pdf_groups = {}
        for pdf_file in pdf_files:
            prefix = pdf_file[:3]
            if prefix not in pdf_groups:
                pdf_groups[prefix] = []
            pdf_groups[prefix].append(pdf_file)
            
            
        # Merge PDFs in each group
        for prefix, files in pdf_groups.items():
            if len(files) > 1:  # Only merge if there are at least two files to merge
                sorted_files = self.sort_files(files)
                merger = PdfMerger()
                for filename in sorted_files:
                    merger.append(os.path.join(pdfs_path, filename))
                
                # Define the merged PDF's name and save path
                merged_pdf_path = os.path.join(pdfs_path, f"{prefix}p_{prefix}s_report.pdf")
                merger.write(merged_pdf_path)
                merger.close()

        

    def delete_files(self, folder_path):
        
        if os.path.exists(folder_path):
            # List all files in the directory
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    # Check if it's a file and then delete it
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
        else:
            print(f"The folder {folder_path} does not exist.")


    def create_folder_reports(self):

        folder_path =  'Withings_reports'
        self.general = 'db/General'
        #source_folder = path.abspath(path.join(self.current_path,
        users = self.current_users()
        self.id_available = users
        print(users)

        
        if os.path.exists(folder_path):
            self.delete_files(folder_path)
        else:
            try:
                os.mkdir(folder_path)
                print('Folder created correctly')
            
            except OSError as error:
                print('Failed to create folder in the path')

        
        for i in range (len(self.id_available)):
            #General database path for the users folders
            new_path = path.abspath(path.join(self.current_path, self.general, self.id_available[i]))

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

    
    def usage_reports(self):
        usage_users = []



        self.usage = 'Usage.csv'


        for i in range (len(self.id_available)):
            #General database path for the users folders
            new_path = path.abspath(path.join(self.current_path, self.general, self.id_available[i], self.usage))
            #print(new_path)
            
            if os.path.exists(new_path):
                # Open the CSV file in read mode
                with open(new_path, 'r', newline='') as csv_file:
                    print(self.id_available[i])
                    df = pd.read_csv(new_path, header = 0, delimiter=',')
                    print('after df')
                    last_row_values = df.iloc[-1].tolist()
                    print('after df 1')

                    usage_users.append(last_row_values)
                    
                    
                    
        # Transpose the dat
        usage_data = list(zip(*usage_users))
        
        # Convert each tuple to a list
        result_usage = [list(column) for column in usage_data]
        print(result_usage)

        start_dates_str = [str(x) for x in result_usage[1]]
        end_dates_str = [str(x) for x in result_usage[2]]
        sleep_last = [str(x) for x in result_usage[6]]
        watch_last = [str(x) for x in result_usage[9]]
        scale_last = [str(x) for x in result_usage[12]]

        #print(sleep_last[-1])
        formatted_start_dates = [(' ' if date_str == 'nan' else datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%b %d')) for date_str in start_dates_str]
        formatted_end_dates = [(' ' if date_str == 'nan' else datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%b %d')) for date_str in end_dates_str]
        formatted_sleeplast_dates = [(' ' if date_str == 'nan'  else datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%b %d')) for date_str in sleep_last]
        formatted_watchlast_dates = [(' ' if date_str == 'nan' else datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%b %d')) for date_str in watch_last]
        formatted_scalelast_dates = [(' ' if date_str == 'nan' else datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%b %d')) for date_str in scale_last]

        print(formatted_start_dates)
        usage_reports = usage_pdf.PDF_Usage(id_user = self.id_available,
                                            path = None,
                                            start_date = formatted_start_dates,
                                            end_date = formatted_end_dates,
                                            sleepmat_usage = result_usage[4],
                                            sleepmat_battery = result_usage[5],
                                            sleepmat_last = formatted_sleeplast_dates,
                                            watch_usage = result_usage[7],
                                            watch_battery = result_usage[8],
                                            watch_last = formatted_watchlast_dates,
                                            scale_usage = result_usage[10],
                                            scale_battery = result_usage[11],
                                            scale_last = formatted_scalelast_dates
                                            )
        
    @classmethod
    def main(cls):
        a = cls(report_type = None,
                   user = None)
        a.individual_report_generation()
        #a.create_folder_reports()
        #a.usage_reports()
        #a.merge_pdf()
		

	
	

if __name__ == "__main__":
    Resilient.main()
            

    


                    

    