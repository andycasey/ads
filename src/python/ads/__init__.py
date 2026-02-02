import logging
import os
from pathlib import Path

debug = False

__version__ = "0.2.dev0"

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

# setup config for first time
CONFIG = Path.home() / ".ads" / "config.json"
if ~os.path.exists(CONFIG):
    from ads.settings import ADSConfig

    os.makedirs(CONFIG.parents[0], exist_ok=True)
    ADSConfig().save(CONFIG)
    print("Generated config at ~/.ads/config.json")


# namespace discovery
from ads.client import SearchQuery
from ads.models import Affiliation, Document, Journal, Library

