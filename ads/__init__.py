import logging
logger = logging.getLogger(__name__)


debug = False

__version__ = "0.13.0"

if debug:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
else:
    logger.addHandler(logging.NullHandler())

