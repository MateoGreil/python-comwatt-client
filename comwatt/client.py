import requests
import json

class ComwattClient:
    def __init__(self):
        self.base_url = 'https://energy.comwatt.com/api'

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

        response = requests.post(url, headers=headers, json=data)
        print(json.dumps(response.json()))
        if response.status_code == 200:
            auth_token = response.json().get('token')
            if auth_token:

                return auth_token
            else:
                raise Exception('Authentication failed: No token received')
        else:
            raise Exception(f'Authentication failed: {response.status_code}')    
