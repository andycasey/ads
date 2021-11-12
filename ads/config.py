import os

# API urls
ADSWS_API_URL = 'https://api.adsabs.harvard.edu/v1'
SEARCH_URL = f'{ADSWS_API_URL}/search/query/'
BIGQUERY_URL = f'{ADSWS_API_URL}/search/bigquery/'
METRICS_URL = f'{ADSWS_API_URL}/metrics/'
EXPORT_URL = f'{ADSWS_API_URL}/export/'

# Token discovery variables
TOKEN_FILES = list(map(os.path.expanduser,
    [
        "~/.ads/token",
        "~/.ads/dev_key",
    ]
))
TOKEN_ENVIRON_VARS = ["ADS_API_TOKEN", "ADS_DEV_KEY"]
token = None  # for setting in-situ

max_rows_per_request = 200