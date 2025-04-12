import pandas as pd
from tqdm import tqdm
import os
import numpy as np

class DataStructureGenerator:
    def __init__(self, base_path, clinic_folder, activity_folder):
        self.base_path = base_path
        self.clinic_folder = clinic_folder
        self.activity_folder = activity_folder
        self.all_data = {}
        

    def generate_data_structure(self):
        clinical_data_path = self.base_path + "\\" + self.clinic_folder + "\Clinic_DataPDBioStampRCStudy.csv"
        
        # Load clinical data
        clinical_data = pd.read_csv(clinical_data_path)
        clinical_data["ID"] = 10
        # Dictionary to store all data
        ret_all_data = {}

        for pid in tqdm(clinical_data["ID"].head(1), desc="Loading participants"):

            pid_str = f"{pid:03d}"  # Formats as 005, 006 etc.
            # pid_str = pid
            participant_path = os.path.join(self.base_path , self.activity_folder, pid_str)
            
            if not os.path.exists(participant_path):
                print(f"\nFolder missing for participant {pid_str}")
                continue
            
            # Initialize participant entry
            ret_all_data[pid_str] = {
                'clinical': clinical_data[clinical_data["ID"] == pid].iloc[0].to_dict(),
                'activity': None}
            
            #     Load annotation file
            anno_file = f"AnnotID{pid_str}.csv"
            full_path_anno = os.path.join(participant_path, anno_file)

            try:
                if os.path.exists(full_path_anno):
                    # Read CSV with exactly the columns shown in your screenshot
                    df_anno = pd.read_csv(full_path_anno) 
                    
                    df_anno_events = df_anno[df_anno['Start Timestamp (ms)'] != df_anno['Stop Timestamp (ms)']]
                    
                    activity_data = []
                    # for index, row in df_anno_events.iterrows():
                    for index, row in df_anno_events.iterrows():
                        event_type = row['EventType']
                        start_time = row['Start Timestamp (ms)']
                        stop_time = row['Stop Timestamp (ms)']
                        df_anno_events_value = df_anno[(df_anno['Start Timestamp (ms)'] == stop_time)]

                        combined_attr = ", ".join(
                        f"{row_event['EventType']} {row_event['Value']}" for _, row_event in df_anno_events_value.iterrows()
                        )

                        sensor_data = self.sensorDataForParticipant(start_time, stop_time, pid_str)
                    
                        new_activity = {
                            'event type': event_type,
                            'start timestamp (ms)': start_time,
                            'stop timestamp (ms)': stop_time,
                            'activity attribute': combined_attr,
                            'sensor data': sensor_data
                        } 
                    
                        # print(event_type)
                        activity_data.append(new_activity)
                        
                    # Convert the activity data to a DataFrame
                    # print(len(activity_data))
                    # for activity in activity_data:
                    #     print(activity)
                    activity_df = pd.DataFrame(activity_data)
                    
                    # print(activity_df.head())
                    # Store the activity data in the participant's entry
                    ret_all_data[pid_str]['activity'] = activity_df
                    
            except Exception as e:
                raise Exception(f"\nError loading {anno_file} for {pid_str}: {str(e)}")    
        return ret_all_data  
    
    def sensorDataForParticipant(self,start_time, stop_time, pid_str):
        # Initialize a dictionary to hold sensor data

        # print('come here 2')
        # Sensor configuration - matches your file naming
        sensors = {
            # 'chest': 'ch',
            # 'left_thigh': 'll', 
            'left_arm': 'lh',
            # 'right_thigh': 'rl',
            'right_arm': 'rh'
        }

        lst_sensor_data = []
        # Iterate through each sensor
        for sensor_name, sensor_prefix in sensors.items():
            # Construct the file name
            sensor_file = f"{sensor_prefix}_ID{pid_str}Accel.csv"
            full_path_sensor = os.path.join(self.base_path, self.activity_folder, pid_str, sensor_file)
            
            # Check if the file exists
            if os.path.exists(full_path_sensor):
                try:
                    # Read the CSV file
                    df_sensor = pd.read_csv(full_path_sensor)
                    
                    # Filter data based on timestamps
                    filtered_sensor_data = df_sensor[(df_sensor['Timestamp (ms)'] >= start_time) & (df_sensor['Timestamp (ms)'] <= stop_time)]
                    if not filtered_sensor_data.empty:
                        filtered_data = filtered_sensor_data.copy()                      
                        filtered_data['Mag'] = np.sqrt(
                        filtered_data['Accel X (g)']**2 +
                        filtered_data['Accel Y (g)']**2 +
                        filtered_data['Accel Z (g)']**2)

                        # Store the filtered data in the dictionary
                        sensor_element = {
                            'sensor name': sensor_name,
                            'sensor data': filtered_data,                           
                        }

                        # Append the sensor data to the list
                        lst_sensor_data.append(sensor_element)
                except Exception as e:
                    print(f"\nError loading {sensor_name} for {pid_str}: {str(e)}")
            else:
                print(f"\nFile not found: {sensor_file} in {pid_str}")

        return lst_sensor_data

 