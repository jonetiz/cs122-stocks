from datetime import datetime, timedelta
import json, os

class StaleCache(Exception):
    def __init__(self, file):
        super().__init__(f"StaleCache Warning: Loaded {file}.json from cache but it is stale.")

def get(file_name, callback=None, callback_expiration=None, *callback_args, **callback_kwargs):
    # try to read file that exists, if it doesn't exist, run the callback with the arguments
    try:
        file_path = 'api/cache/' + file_name + '.json'
        with open(file_path, 'r') as f:
            data = json.load(f)
    except:
        # if callback is defined, execute and cache it
        if callback:
            data = callback(*callback_args, **callback_kwargs)
            cache(file_name, data, callback_expiration)
            return data
    
    expires: float = data.get('expires')
    if expires:
        if expires < datetime.now().timestamp():
            raise StaleCache(file_name)

    return data['data']

def cache(file_name: str, data: dict, expires: datetime | bool = None):
    # if no expiration set, expire at 2 am the next day (because both APIs compile previous day data around midnight)
    if expires is None:
        now = datetime.now()
        expires = (datetime(now.year, now.month, now.day) + timedelta(days=1, hours=2)).timestamp()

    file_path = 'api/cache/' + file_name + '.json'

    with open(file_path, 'w+') as f:
        json.dump({'expires': expires, 'data': data}, f)

def invalidate(file_name):
    # invalidate (delete) a cached file
    os.remove('api/cache' + file_name + '.json')