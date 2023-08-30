from dotenv import load_dotenv
import json
import os

load_dotenv()

REQUEST_TIMEOUT = 3  # three second timeout
RESCALE = "0,50"
TITILER_ENDPOINT = os.getenv("TITILER_ENDPOINT")
TITILER_STAC_ENDPOINT = os.getenv("TITILER_STAC_ENDPOINT")
STAC_CATALOG = (
    json.loads(os.getenv("STAC_CATALOG")) if os.getenv("STAC_CATALOG") else None
)
