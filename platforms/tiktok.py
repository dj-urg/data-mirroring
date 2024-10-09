import json
import pandas as pd

def process_tiktok_file(file):
    # Read the JSON file
    data = json.load(file)
    # Convert to DataFrame
    df = pd.json_normalize(data)
    # Save to CSV
    csv_file_path = 'downloads/output.csv'
    df.to_csv(csv_file_path, index=False)
    return df, csv_file_path