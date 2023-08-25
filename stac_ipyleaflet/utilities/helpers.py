import csv
from importlib.resources import files
from ipyleaflet import TileLayer
import logging
import requests
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


def add_layers_options(add_layer, file_name):
    layers_file = files("stac_ipyleaflet.utilities.data").joinpath(file_name)
    with open(layers_file, newline="") as f:
        csv_reader = csv.reader(f)
        next(csv_reader, None)  # skip the headers
        sorted_csv = sorted(csv_reader, key=lambda row: row[0], reverse=True)
        for row in sorted_csv:
            name, tile_url = row[0], row[1]
            tile_layer = TileLayer(
                url=tile_url, attribution=name, name=name, visible=False
            )
            add_layer(tile_layer)
    return
