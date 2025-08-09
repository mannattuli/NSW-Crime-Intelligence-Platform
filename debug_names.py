import pandas as pd

# Normalizes suburb names for consistent merging across datasets.
def clean_suburb_name(suburb_name_series: pd.Series) -> pd.Series:
    cleaned_suburb_series = suburb_name_series.str.upper().str.strip()
    cleaned_suburb_series = cleaned_suburb_series.str.replace(r' \(.*\)', '', regex=True)
    return cleaned_suburb_series

# Loads crime, SEIFA, and premises files and reports overlaps in cleaned suburb names.
def debug_the_merge() -> None:
    print("--- Running Suburb Name Debugger ---")

    processed_crime_file_path = 'crime_data_processed.parquet'
    seifa_file_path = 'ABS_ABS_SEIFA2016_SSC_1.0.0.csv'
    premises_file_path = 'premises-list-as-at-8-february-2021.csv'

    print("\n[1] Loading Crime Data...")
    crime_dataframe = pd.read_parquet(processed_crime_file_path)
    cleaned_crime_series = clean_suburb_name(crime_dataframe['Suburb'].dropna())
    crime_suburbs = set(cleaned_crime_series.unique())
    print(f"Found {len(crime_suburbs)} unique suburbs.")
    print("Sample:", sorted(list(crime_suburbs))[:5])

    print("\n[2] Loading SEIFA Data...")
    seifa_dataframe = pd.read_csv(seifa_file_path)
    cleaned_seifa_series = clean_suburb_name(seifa_dataframe['State Suburb'].dropna())
    seifa_suburbs = set(cleaned_seifa_series.unique())
    print(f"Found {len(seifa_suburbs)} unique suburbs.")
    print("Sample:", sorted(list(seifa_suburbs))[:5])

    print("\n[3] Loading Premises Data...")
    premises_dataframe = pd.read_csv(premises_file_path, encoding='latin1')
    cleaned_premises_series = clean_suburb_name(premises_dataframe['Suburb'].dropna())
    premises_suburbs = set(cleaned_premises_series.unique())
    print(f"Found {len(premises_suburbs)} unique suburbs.")
    print("Sample:", sorted(list(premises_suburbs))[:5])

    print("\n--- Merge Analysis ---")
    crime_seifa_overlap = crime_suburbs.intersection(seifa_suburbs)
    print(f"Overlap between Crime and SEIFA data: {len(crime_seifa_overlap)} suburbs.")

    crime_premises_overlap = crime_suburbs.intersection(premises_suburbs)
    print(f"Overlap between Crime and Premises data: {len(crime_premises_overlap)} suburbs.")

    if len(crime_seifa_overlap) == 0:
        print("\n--- Example Crime Suburbs NOT Found in SEIFA Data ---")
        unmatched_suburbs = sorted(list(crime_suburbs - seifa_suburbs))
        print(unmatched_suburbs[:20])
        print("...")

if __name__ == "__main__":
    debug_the_merge()


