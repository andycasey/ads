"""
configuration
"""
import os

# API urls
ADSWS_API_URL = 'https://api.adsabs.harvard.edu/v1'
SEARCH_URL = '{}/search/query/'.format(ADSWS_API_URL)
BIGQUERY_URL = '{}/search/bigquery/'.format(ADSWS_API_URL)
METRICS_URL = '{}/metrics/'.format(ADSWS_API_URL)
EXPORT_URL = '{}/export/'.format(ADSWS_API_URL)

# Token discovery variables
TOKEN_FILES = list(map(os.path.expanduser,
    [
        "~/.ads/token",
        "~/.ads/dev_key",
    ]
))
TOKEN_ENVIRON_VARS = ["ADS_API_TOKEN", "ADS_DEV_KEY"]
token = None  # for setting in-situ
