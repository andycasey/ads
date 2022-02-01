import logging


debug = False

__version__ = "0.13.0"

if debug:
    level = logging.DEBUG
    logging.basicConfig(level=level)
    logging.root.setLevel(level)
    logging.basicConfig(level=level)
    logger = logging.getLogger(__name__)
    """
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    """
    
else:
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())

from ads.models import (Affiliation, Document, Journal, Library)
from ads.client import SearchQuery