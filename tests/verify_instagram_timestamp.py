
import pandas as pd
import numpy as np

def verify_timestamp_handling():
    # Simulate a dataframe with datetime objects as used in analysis
    data = {
        'timestamp': pd.to_datetime(['2023-01-01 12:00:00', '2023-01-02 13:00:00']),
        'title': ['Test1', 'Test2']
    }
    df = pd.DataFrame(data)
    
    # --- Current Logic Simulation (Analysis using datetime timestamp) ---
    print("Verifying analysis logic...")
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['month'] = df['timestamp'].dt.month
    df['year'] = df['timestamp'].dt.year
    
    expected_days = ['Sunday', 'Monday']
    if list(df['day_of_week']) == expected_days:
        print("[PASS] Analysis logic works correctly with datetime objects.")
    else:
        print(f"[FAIL] Analysis logic failed. Got {list(df['day_of_week'])}")
        return

    # --- Proposed Fix Simulation ---
    # We do NOT add unix_timestamp to the main df
    
    # Check what goes to preview
    print("\nVerifying preview data safety...")
    if 'unix_timestamp' not in df.columns:
        print("[PASS] unix_timestamp is NOT in main DataFrame (safe for preview).")
    else:
        print("[FAIL] unix_timestamp IS in main DataFrame.")
        return

    # Check export logic simulation
    print("\nVerifying export logic...")
    df_export = df.copy()
    # Add unix_timestamp ONLY to export copy
    df_export['unix_timestamp'] = df_export['timestamp'].astype('int64') // 10**9
    
    if 'unix_timestamp' in df_export.columns:
        print("[PASS] unix_timestamp is present in export DataFrame.")
        print(f"Sample value: {df_export['unix_timestamp'][0]}")
    else:
        print("[FAIL] unix_timestamp missing from export.")

if __name__ == "__main__":
    verify_timestamp_handling()
