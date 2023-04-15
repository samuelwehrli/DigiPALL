# https://developer.corsano.com/rest/intro/

import requests, datetime
import pandas as pd


def dict2urlparams(params):
    if params:
        out = '?'
        for k, v in params.items():
            if isinstance(v, list):
                for i, el in enumerate(v):
                    out += f'{k}[{i}]={el}&'
            else:
                out += f'{k}={v}&'
        return out[:-1]
    else:
        return ''


def get_slots(data, key=None):
    # this function is not used ...
    if type(data) is dict:
        if 'slots' in data:
            df = pd.DataFrame(data['slots'])
            df.insert(0, 'type', key)
            return df
        else:
            return pd.concat([get_slots(v,k) for k,v in data.items()])
    elif type(data) is list:
        return pd.concat([get_slots(d) for d in data])
    else:
        return pd.DataFrame()


def init_with_login(email, password):
    """
    Initialize the Users and Health APIs

    :param email
    :param password
    :return: uapi, hapi, error
    """
    error = None
    uapi = UsersAPI()
    hapi = HealthAPI()
    uapi.login(email, password)

    if uapi.token:
        hapi.login(uapi.token)
    else:
        error = 'Users API Login failed'

    if not hapi.token:
        error = 'Health API Login failed'

    return uapi, hapi, error


class UsersAPI:
    BASE_URL = r'https://api.users.cloud.corsano.com/'

    def __init__(self):
        self.token = None

    def post(self, path, data):
        url = self.BASE_URL + path
        headers = {'Content-Type': 'application/json'}
        return requests.post(url, json=data, headers=headers).json()

    def login(self, email, password):
        data = {'email': email, 'password': password}
        res = self.post('login', data)
        if 'token' in res:
            self.token = res['token']
        return res



class HealthAPI:
    BASE_URL = r'https://api.health.cloud.corsano.com/'

    def __init__(self):
        self.token = None

    def post(self, path, data):
        url = self.BASE_URL + path
        headers = {'Content-Type': 'application/json'}
        return requests.post(url, json=data, headers=headers).json()

    def get(self, path, params=None):
        url = self.BASE_URL + path + dict2urlparams(params)
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return requests.get(url, headers=headers).json()

    def login(self, user_api_token):
        data = {'user_api_token': user_api_token}
        res = self.post('login', data)
        if 'token' in res:
            self.token = res['token']
        return res

    def user_summaries(self, date_from, date_to, include_slots=0, per_page=10, page=1, types=None):
        params = {
            'date_from': date_from,
            'date_to': date_to,
            'include_slots': include_slots,
            'per_page': per_page,
            'page': page,
        }
        if types:
            params['types'] = types
        return self.get('user-summaries', params)

    # function which returns the data in a dataframe starting n days ago and for a given measurement type
    def get_data(self, from_days_ago, measurement_type):
        """
        reads data in dict which is easily converted to a dataframe

        :param from_days_ago: number of days to go back
        :param measurement_type: heart_rate, activity, ...
        :return: data in dict format
        """
        today = datetime.date.today()
        date_from = today - datetime.timedelta(days=from_days_ago)

        res = self.user_summaries(date_from.isoformat(), today.isoformat(), types=[measurement_type], per_page=from_days_ago+1)
        data = []
        for el in res['data']:
            date = el['date']
            # calculate days ago from date
            days_ago = (today - datetime.date.fromisoformat(date)).days
            tmp = {'date': date, 'days_ago': days_ago}
            tmp.update(el[measurement_type])
            data.append(tmp)

        return data






