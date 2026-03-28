import pandas as pd
import numpy as np
import os

def create_training_set():
    # 1. Create the /ml directory if it doesn't exist
    if not os.path.exists('ml'):
        os.makedirs('ml')
        print("Created /ml directory")

    all_data = []
    files = ['collect1.txt', 'collect2.txt', 'collect3.txt', 'collect4.txt', 
             'collect5.txt', 'collect6.txt', 'collect7.txt']

    for f in files:
        if os.path.exists(f):
            # Read file, skipping comments (#) and metadata ([tags])
            df = pd.read_csv(f, comment='#', skip_blank_lines=True)
            # Filter out any rows that accidentally caught metadata tags
            df = df[~df['id'].astype(str).str.contains(r'\[', na=False)]
            all_data.append(df)

    if not all_data:
        print("No data found to merge.")
        return

    master_df = pd.concat(all_data, ignore_index=True)

    # ML Processing
    master_df['timestamp'] = pd.to_datetime(master_df['timestamp'])
    master_df['hour'] = master_df['timestamp'].dt.hour
    master_df['hour_sin'] = np.sin(2 * np.pi * master_df['hour']/24.0)
    master_df['hour_cos'] = np.cos(2 * np.pi * master_df['hour']/24.0)
    master_df = master_df.dropna()

    # 2. Save specifically to the /ml folder
    output_path = os.path.join('ml', 'training_set.csv')
    master_df.to_csv(output_path, index=False)
    print(f"Success! {output_path} created with {len(master_df)} rows.")

if __name__ == "__main__":
    create_training_set()
