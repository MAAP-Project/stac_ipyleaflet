from dotenv import load_dotenv
import json
import os

load_dotenv()

REQUEST_TIMEOUT = 3  # three second timeout
RESCALE = "0,50"
TITILER_ENDPOINT = os.getenv("TITILER_ENDPOINT")
TITILER_STAC_ENDPOINT = os.getenv("TITILER_STAC_ENDPOINT")
STAC_CATALOG = {"name": os.getenv("STAC_CATALOG_NAME"), "url": os.getenv("STAC_CATALOG_URL")}
STAC_BROWSER_URL = os.getenv("STAC_BROWSER_URL")
