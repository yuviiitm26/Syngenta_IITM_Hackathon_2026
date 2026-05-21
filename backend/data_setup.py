import sqlite3
import pandas as pd
import os

print("Initializing Production Data Warehouse...")

# Connect to the database (this creates syngenta_prod.db)
conn = sqlite3.connect("syngenta_prod.db")

# Tell Python the name of the folder containing your CSVs
data_folder = "data"

# Define all your actual hackathon files pointing inside the 'data' folder
files_to_load = {
    "growers": os.path.join(data_folder, "growers.csv"),
    "retailers": os.path.join(data_folder, "retailers.csv"),
    "territories": os.path.join(data_folder, "reps_territory.csv"),
    "inventory": os.path.join(data_folder, "retailer_inventory_weekly.csv"),
    "visits": os.path.join(data_folder, "retailer_visit_log.csv"),
    "digital_funnel": os.path.join(data_folder, "digital_funnel_weekly.csv"),
    "whatsapp_campaign": os.path.join(data_folder, "whatsapp_campaign.csv")
}

# The ETL Loop: Read CSV -> Clean -> Push to SQL Table
for table_name, file_path in files_to_load.items():
    try:
        print(f"Loading {file_path} into table '{table_name}'...")
        # Pandas reads the file from the correct folder
        df = pd.read_csv(file_path)
        
        # Automatically creates the SQL table schema and inserts the data
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"✓ Success: {len(df)} rows loaded.")
        
    except FileNotFoundError:
        print(f"⚠️ Warning: '{file_path}' not found. Make sure the 'data' folder is in the same directory as this script.")

conn.close()
print("\nData Warehouse build complete. All tables are live.")