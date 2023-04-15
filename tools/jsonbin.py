import requests

class BinAPI:
    BASE_URL = r'https://api.jsonbin.io/v3/b'

    def __init__(self, api_key, bin_id):
        self.api_key = api_key
        self.bin_id = bin_id
        self.bin_url = self.BASE_URL + '/' + self.bin_id

    def read(self):
        url = self.bin_url + '/latest'
        headers = { 'X-Master-Key': self.api_key }
        res = requests.get(url, headers=headers).json()
        return res['record']

    def update(self, data):
        url = self.bin_url
        headers = { 'X-Master-Key': self.api_key, 'Content-Type': 'application/json'}
        res = requests.put(url, headers=headers, json=data).json()
        return res

