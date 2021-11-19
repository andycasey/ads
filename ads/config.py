import os

ADSWS_API_URL = 'https://api.adsabs.harvard.edu/v1'

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