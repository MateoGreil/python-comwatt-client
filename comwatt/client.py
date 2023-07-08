import requests
import json

class ComwattClient:
    def __init__(self):
        self.base_url = 'https://energy.comwatt.com/api'
        self.session = requests.Session()

    # Password should be encrypted password, I don't know exactly what the encryption is for the moment,
    # so you will need to encrypt it from their webapp
    def authenticate(self, username, password):
        url = f'{self.base_url}/v1/authent'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/json;charset=utf-8',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        data = {'username': username, 'password': password}

        response = self.session.post(url, headers=headers, json=data)

        if response.status_code != 200:
            raise Exception(f'Authentication failed: {response.status_code}')    

    def get_authenticated_user(self):
        url = f'{self.base_url}/users/authenticated'

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving authenticated user: {response.sttaus_code}')

    def get_sites(self):
        url = f'{self.base_url}/sites'

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving sites: {response.sttaus_code}')

    def get_devices(self, site_id):
        url = f'{self.base_url}/devices?siteId={site_id}'

        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error retrieving sites: {response.sttaus_code}')
