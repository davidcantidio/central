
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_google_sheets_config_data():
    # Load configurations from config.json file
    with open('config.json') as json_data_file:
        google_config = json.load(json_data_file)
    return google_config
    
# Authenticate and open Google Sheets spreadsheet
def authenticate_google_sheets(google_config):
    # Get the scopes from the config data
    scopes = google_config['scopes']

    # Authenticate and open Google Sheets spreadsheet
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_config, scopes)
    client = gspread.authorize(credentials)
    return client


def open_spreadsheet(auth_client, google_config):
    spreadsheet = auth_client.open_by_key(google_config['googleSheets']['spreadsheetId'])
    
    return spreadsheet

#Get the Instagram ID for all clients active, with permissions and under "Redes Sociais" contract
def get_filtered_instagram_ids(spreadsheet):
    # Get all values from the worksheet
    all_values = spreadsheet.sheet1.get_all_records()  # Assume you are working with the first worksheet. Adjust the index if needed.    # Filter the data based on conditions (ativo=True, permissoes=True, redesSociais=True)
    filtered_data = [record['IDInstagram'] for record in all_values if record.get('IDInstagram') and record.get('Ativo') and record.get('permissoes') and record.get('redesSociais')]

    return filtered_data