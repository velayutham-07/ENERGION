# test_with_proxy_fixed.py
import gspread
from google.oauth2.service_account import Credentials
import os

# ============================================
# ADD YOUR PROXY HERE (if you have one)
# ============================================
# If you have a proxy, uncomment and add your proxy details:
# os.environ['HTTP_PROXY'] = 'http://proxy.yourcompany.com:8080'
# os.environ['HTTPS_PROXY'] = 'http://proxy.yourcompany.com:8080'

# Alternative: Use system proxy
os.environ['REQUESTS_CA_BUNDLE'] = ''  # Bypass SSL verification for testing

SERVICE_ACCOUNT_FILE = 'bog-project-491510-8cb3cd7a9aa7.json'

try:
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    client = gspread.authorize(creds)
    
    # Test with one sheet
    sheet_id = '1JlFXOqjEGQappPdb2N7xIjbFyxPkK0oFuLEWMmfVsfQ'
    sheet = client.open_by_key(sheet_id)
    print(f"✅ Connected to: {sheet.title}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nIf you're behind a corporate proxy, add it to the code.")