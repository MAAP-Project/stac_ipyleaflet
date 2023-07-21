import requests
import logging
from stac_ipyleaflet.constants import REQUEST_TIMEOUT

def make_get_request(url, params=None, timeout=REQUEST_TIMEOUT):
    """GET Request wrapper to watch for and catch specific errors
    Args:
        url (str): HTTP URL to a STAC item
        params (dict[str, Any]): request parameters
        timeout: duration for requests to stop waiting for a response after a given number of seconds
    """
    try:
        req = requests.get(url, params=params, timeout=timeout)
        return req
    except requests.exceptions.Timeout:
        # QUESTION: Should we retry?
        logging.error(f"timeout raised during get request")
    except requests.exceptions.RequestException as e:
        logging.error(e)
    return None