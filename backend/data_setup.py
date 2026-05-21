from config import logger
import pandas as pd
import sqlite3
import os

logger.info("Initializing Production Data Warehouse...")

def load_csv_to_sqlite(file_path, table_name, conn):
    if os.path.exists(file_path):
        logger.info(f"Loading {file_path} into table '{table_name}'...")
        df = pd.read_csv(file_path)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        logger.info(f"✓ Success: {len(df)} rows loaded.")
    else:
        logger.warning(f"⚠️ Warning: '{file_path}' not found. Make sure the 'data' folder is in the same directory as this script.")

def main():
    conn = sqlite3.connect('syngenta_prod.db')
    
    # Check if we are running from root or backend directory
    prefix = 'backend/' if os.path.exists('backend/data') else ''
    
    data_files = {
        f'{prefix}data/growers.csv': 'growers',
        f'{prefix}data/retailers.csv': 'retailers',
        f'{prefix}data/retailer_inventory_weekly.csv': 'inventory',
        f'{prefix}data/reps_territory.csv': 'territories',
        f'{prefix}data/retailer_pos.csv': 'pos_data',
        f'{prefix}data/retailer_visit_log.csv': 'visits',
        f'{prefix}data/digital_funnel_weekly.csv': 'digital_funnel',
        f'{prefix}data/whatsapp_campaign.csv': 'campaigns'
    }

    for file_path, table_name in data_files.items():
        load_csv_to_sqlite(file_path, table_name, conn)

    conn.close()
    logger.info("Data Warehouse build complete. All tables are live.")

if __name__ == "__main__":
    main()
