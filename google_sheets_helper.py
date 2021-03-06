import os, sys
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import settings

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class GoogleSheetsHelper(object):

    def __init__(self):
        self.credentials = self.get_credentials()

    def get_credentials(self):
        """
        Gets credentials to be used for making calls to google sheets api
        :return: credentials
        """
        if getattr(self, 'credentials', None):
            return self.credentials

        scopes = settings.SCOPES
        client_secret_file = settings.CLIENT_SECRET_FILE
        application_name = 'Google Sheets API Python Quickstart'

        home_dir = os.path.expanduser(settings.CREDENTIALS_DIRECTORY)
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, 'sheets.googleapis.com-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(client_secret_file, scopes)
            flow.user_agent = application_name
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            # print('Storing credentials to ' + credential_path)
        return credentials

    def update_koinex_google_sheet(self, price_data):
        """
        Updates the prices of coins given in the spreadsheet indicated. Supported coins
        are: BTC, XRP, LTC, ETH, BCH
        :param price_data: A dictionary containg key as abbrv of coins and values as their price
        :return: None
        """
        credentials = getattr(self, 'credentials', self.get_credentials())
        http = credentials.authorize(httplib2.Http())
        discovery_url = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discovery_url)
        spreadsheet_ids = settings.SPREADSHEET_IDS
        range_name = 'Overall!B2:B14'
        value_input_option = 'RAW'
        value_range_body = {
            "range": "Overall!B2:B14",
            "majorDimension": "COLUMNS",
            "values": [[price_data['BTC'], price_data['XRP'], price_data['LTC'], price_data['ETH'], price_data['BCH'],
                price_data['GNT'], price_data['OMG'], price_data['REQ'], price_data['ZRX'], price_data['BAT'], price_data['TRX'], price_data['AE']]]
        }
        for spreadsheet_id in spreadsheet_ids:
            request = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption=value_input_option, body=value_range_body)
            request.execute()

    def get_price_alerts(self):
        """
        Gets prices for coins to be used for alerts. The data should be in columnar format
        with the first column containing the abbrv of the coin in all caps i.e. BTC
        The second and third column should contain the max price and min price of the coin 
        respectively. The price should be in decimal format, i.e. 13000000.00
        :return: 
        """
        spreadsheet_id = settings.PRICE_ALERT_SPREADSHEET
        credentials = getattr(self, 'credentials', self.get_credentials())
        http = credentials.authorize(httplib2.Http())
        discovery_url = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discovery_url)
        range_name = 'Overall!A24:C34'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        return values

