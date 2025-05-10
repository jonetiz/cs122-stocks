from datetime import datetime, timedelta
import json, os

class CacheNotFound(Exception):
    """This exception is thrown when a file does not exist in cache."""

    def __init__(self, file):
        super().__init__(f"CacheNotFound Error: {file}.json was not found in the cache.")

class StaleCache(Exception):
    """This exception is thrown when a stale file is loaded from cache without a callback defined on the getter."""

    def __init__(self, file):
        super().__init__(f"StaleCache Warning: Loaded {file}.json from cache but it is stale.")

def get(file_name: str, callback = None, callback_expiration: datetime = None, *callback_args, **callback_kwargs) -> dict:
    """Retrieves data from cache at the specified file name; if the data doesn't exist or has expired, it will execute the passed callback method.
    If callback is undefined, it will try to retrieve data via the callback, cache that, and return it.
    """

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
        
        # callback not defined, raise CacheNotFound
        raise CacheNotFound(file_name)
    
    # check expiration
    expires: float = data.get('expires')
    if expires:

        # if the cache is expired
        if expires < datetime.now().timestamp():
            invalidate(file_name)

            # if callback is defined, executee and cache it
            if callback:
                data = callback(*callback_args, **callback_kwargs)
                cache(file_name, data, callback_expiration)
                return data
            
            # callback not defined, raise StaleCache
            raise StaleCache(file_name)

    # return data property since cache is structured as {expires: 0, data: {}}
    return data['data']

def cache(file_name: str, data: dict, expires: datetime | bool = None):
    """Cache data as a json file"""

    # if no expiration set, default expire at midnight
    if expires is None:
        now = datetime.now()
        expires = (datetime(now.year, now.month, now.day) + timedelta(days=1, hours=0)).timestamp()

    file_path = 'api/cache/' + file_name + '.json'

    # save the cached data to the file
    with open(file_path, 'w+') as f:
        json.dump({'expires': expires, 'data': data}, f)

def invalidate(file_name):
    """Invalidates (deletes) a cached file"""

    os.remove('api/cache/' + file_name + '.json')

def update(file_name: str, data: dict, callback=None, callback_expiration=None, *callback_args, **callback_kwargs):
    """Updates the cache without overwriting/appends data"""

    # get current cached data
    cached_data = get(file_name, callback, callback_expiration, *callback_args, **callback_kwargs)
    
    # update cached_data with data and recache
    cached_data.update(data)
    cache(file_name, cached_data, callback_expiration)