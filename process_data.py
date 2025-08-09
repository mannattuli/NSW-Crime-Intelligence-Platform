# process_data.py

import pandas as pd
import sys

INPUT_FILE = 'suburbdata25q1.csv'
OUTPUT_FILE = 'crime_data_processed.parquet'

def process_crime_data(input_path):
    """
    Loads the crime data, forcing the first row to be the header,
    then melts and cleans it for analysis.
    """
    print(f"Loading data from {input_path}...")
    
    try:
        # Force pandas to use the very first row (index 0) as the header.
        df = pd.read_csv(input_path, header=0) 
    except Exception as e:
        print(f"❌ Failed to load CSV. Error: {e}")
        sys.exit()

    print("✅ Data loaded correctly! Reshaping data (melting)...")
    
    # Define the identifier columns based on the now-correct header
    id_vars = ['Suburb', 'Offence category', 'Subcategory']
    date_cols = [col for col in df.columns if col not in id_vars]

    # Melt the dataframe to convert it to a 'long' format
    long_df = pd.melt(df, id_vars=id_vars, value_vars=date_cols, var_name='Date', value_name='Incidents')

    print("Cleaning and transforming data...")
    # Convert 'Date' column from 'Jan 1995' format to proper datetime objects
    long_df['Date'] = pd.to_datetime(long_df['Date'], format='%b %Y')
    
    # Convert 'Incidents' to numbers, turning any errors (like '-') into not-a-number (NaN)
    long_df['Incidents'] = pd.to_numeric(long_df['Incidents'], errors='coerce')
    
    # Clean up the data
    long_df.dropna(subset=['Incidents'], inplace=True) # Drop rows where Incidents is NaN
    long_df = long_df[long_df['Incidents'] > 0] # Keep only rows where at least one incident occurred
    long_df['Incidents'] = long_df['Incidents'].astype(int) # Convert to a whole number

    # Clean up column names for easier use in the app
    long_df.rename(columns={'Offence category': 'OffenceCategory'}, inplace=True)
    
    print(f"Processing complete. Found {len(long_df)} incident records.")
    return long_df

if __name__ == "__main__":
    processed_df = process_crime_data(INPUT_FILE)
    print(f"Saving processed data to {OUTPUT_FILE}...")
    processed_df.to_parquet(OUTPUT_FILE)
    print("✅ All Done! Your data is processed. You can now run the Streamlit app.")