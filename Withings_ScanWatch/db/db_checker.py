import os
import pandas as pd
from datetime import datetime

# Define the root folder containing participant folders
root_folder = "/home/nathalia/Withings_ScanWatch/Withings_ScanWatch/db/General"

# Loop through each participant folder
for participant_folder in os.listdir(root_folder):
    participant_path = os.path.join(root_folder, participant_folder)
    
    # Ensure it's a directory
    if os.path.isdir(participant_path):
        intra_activity_path = os.path.join(participant_path, "Sleepmat_intra_activity.csv")
        summary_path = os.path.join(participant_path, "SleepMat_summary.csv")
        
        # Check if both files exist
        if os.path.exists(intra_activity_path) and os.path.exists(summary_path):
            # Load intra-activity data
            intra_df = pd.read_csv(intra_activity_path)
            summary_df = pd.read_csv(summary_path)
            
            # Find the latest timestamp across all relevant columns
            timestamp_columns = ["startdate", "enddate", "Heart Rate date", "Respiration rate date", "Snoring date"]
            
            # Convert timestamps to numeric (handle errors)
            for col in timestamp_columns:
                intra_df[col] = pd.to_numeric(intra_df[col], errors='coerce')  # Convert to numeric, set invalid values to NaN

            # Get the latest timestamp (max value) for each column
            latest_intra_dates = intra_df[timestamp_columns].max(skipna=True).fillna(0).to_dict()

            print(f"Latest timestamps from intra-activity file for {participant_folder}:")
            print(latest_intra_dates)

            # Extract the last date from the summary file
            last_summary_date_str = summary_df.iloc[-1]["date"]
            
            # Convert summary date to timestamp
            last_summary_timestamp = int(datetime.strptime(last_summary_date_str[:19], "%Y-%m-%dT%H:%M:%S").timestamp())

            # Compute differences in **days**, handling missing values properly
            differences_in_days = {
                key: (last_summary_timestamp - int(value)) / 86400 if value != 0 else None
                for key, value in latest_intra_dates.items()
            }

            print(f"Participant: {participant_folder}")
            print("Time differences in days (summary - intra_activity):")
            print(differences_in_days)
            print("-" * 50)
