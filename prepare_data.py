import pandas as pd
import numpy as np
import os

def create_training_set():
    all_data = []
    # Targeting your specific file naming convention
    files = ['collect1.txt', 'collect2.txt', 'collect3.txt', 'collect4.txt', 
             'collect5.txt', 'collect6.txt', 'collect7.txt']

    for f in files:
        if os.path.exists(f):
            # Skip the # comments and [tags] by using comment parameter
            df = pd.read_csv(f, comment='#', skip_blank_lines=True)
            # Remove lines that contain the tag like '[sim]' or '[open_meteo]'
            df = df[~df['id'].astype(str).str.contains('\[')]
            all_data.append(df)

    # Merge all 7 files
    master_df = pd.concat(all_data, ignore_index=True)

    # --- ML IMPROVEMENTS ---
    # 1. Convert timestamp to datetime
    master_df['timestamp'] = pd.to_datetime(master_df['timestamp'])
    
    # 2. Extract Hour and create Cyclical Features
    master_df['hour'] = master_df['timestamp'].dt.hour
    master_df['hour_sin'] = np.sin(2 * np.pi * master_df['hour']/24.0)
    master_df['hour_cos'] = np.cos(2 * np.pi * master_df['hour']/24.0)

    # 3. Clean up: Remove any rows with missing values
    master_df = master_df.dropna()

    # Save the consolidated training set
    master_df.to_csv('training_set.csv', index=False)
    print(f"Success! Training set created with {len(master_df)} rows.")

if __name__ == "__main__":
    create_training_set()
