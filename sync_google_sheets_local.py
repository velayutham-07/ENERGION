import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import os
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================
SERVICE_ACCOUNT_FILE = 'bog-project-491510-8cb3cd7a9aa7.json'

SHEET_IDS = {
    'Observations': '1JlFXOqjEGQappPdb2N7xIjbFyxPkK0oFuLEWMmfVsfQ',
    'Summary': '1FdBtWtJce_U0iqDvCVex6Uw9UnsiyyaO339yPGc2iQs',
    'Anomalies': '1mtBk7Gjy6MAxR_lnHWPiYLC2ET7dPXenxZ_QNDKgrQI',
    'Insights': '1d_2jqU0X5L6R90zcvBp38baJSwe-xLlKE7IiXDxNIqc'
}

LOCAL_DATA_DIR = 'local_data'

# Create local data directory
os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

# ============================================
# CONNECT TO GOOGLE SHEETS
# ============================================
def connect_to_sheets():
    """Connect to Google Sheets"""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return gspread.authorize(creds)

# ============================================
# SYNC FUNCTIONS
# ============================================
def sync_sheet_to_local(client, sheet_name, sheet_id):
    """Sync a single sheet to local CSV"""
    try:
        print(f"Syncing {sheet_name}...")
        
        # Open sheet and get first worksheet
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        
        # Get all records
        records = worksheet.get_all_records()
        
        if not records:
            print(f"  ⚠️ No data in {sheet_name}")
            return False
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Save to CSV
        csv_path = os.path.join(LOCAL_DATA_DIR, f'{sheet_name}.csv')
        df.to_csv(csv_path, index=False)
        
        # Also save as JSON for easy reading
        json_path = os.path.join(LOCAL_DATA_DIR, f'{sheet_name}.json')
        df.to_json(json_path, orient='records', indent=2)
        
        print(f"  ✅ Saved {len(df)} rows to {csv_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error syncing {sheet_name}: {e}")
        return False

def sync_all_sheets():
    """Sync all 4 sheets to local files"""
    print("=" * 50)
    print("Syncing Google Sheets to Local")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    client = connect_to_sheets()
    
    results = {}
    for sheet_name, sheet_id in SHEET_IDS.items():
        results[sheet_name] = sync_sheet_to_local(client, sheet_name, sheet_id)
    
    print("=" * 50)
    print("Sync Complete!")
    print(f"Data saved to: {LOCAL_DATA_DIR}/")
    print("=" * 50)
    
    return results

# ============================================
# READ LOCAL DATA FUNCTIONS
# ============================================
def load_local_observations():
    """Load observations from local CSV"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Observations.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

def load_local_summary():
    """Load summary from local CSV"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Summary.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

def load_local_anomalies():
    """Load anomalies from local CSV"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Anomalies.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

def load_local_insights():
    """Load insights from local CSV"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Insights.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

# ============================================
# RUN SYNC
# ============================================
if __name__ == "__main__":
    # Sync once
    sync_all_sheets()
    
    # Example: Load and display local data
    print("\n" + "=" * 50)
    print("LOCAL DATA PREVIEW")
    print("=" * 50)
    
    obs = load_local_observations()
    if not obs.empty:
        print(f"\nObservations: {len(obs)} rows")
        print(obs.head())
    
    summary = load_local_summary()
    if not summary.empty:
        print(f"\nSummary: {len(summary)} rows")
        print(summary.tail())