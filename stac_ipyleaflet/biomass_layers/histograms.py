import csv
import re
from io import BytesIO

import numpy
import numpy.ma as ma
import requests
import rioxarray
import xarray as xr
from ipywidgets import (
    Checkbox,
    DatePicker,
    Dropdown,
    HBox,
    jslink,
    Layout,
    Output,
    Text,
    Textarea,
    ToggleButtons,
    VBox,
)
from ipyleaflet import (
    Popup,
    display
)
from rio_tiler.io import Reader
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from ..base_widget import TileLayer

class Histograms():
    def update_selected_data(self):
        layers = self.layers
        # TODO(aimee): if geometry hasn't changed and a previously selected layer is still selected, don't re-fetch it.
        self.selected_data = []
        visible_layers = [
            layer
            for layer in layers
            if type(layer) == TileLayer and layer.visible and not layer.base
        ]
        geometries = [self.draw_control.last_draw["geometry"]]
        if geometries[0]:
            box = Polygon(geometries[0]["coordinates"][0])
            # https://shapely.readthedocs.io/en/latest/reference/shapely.bounds.html?highlight=bounds#shapely.bounds
            # For geometries these 4 numbers are returned: min x, min y, max x, max y.
            bounds = box.bounds
            self.bbox_centroid = [box.centroid.y, box.centroid.x]

            if len(visible_layers) != 0:
                self.loading_widget_layer.location = self.bbox_centroid
                if self.loading_widget_layer not in self.layers:
                    self.add_layer(self.loading_widget_layer)
                else:
                    self.loading_widget_layer.open_popup()

            for idx, layer in enumerate(visible_layers):
                layer_url = layer.url
                ds = None
                title = layer.name.replace("_", " ").upper()
                match = re.search("url=(.+.tif)", layer_url)
                if match and match.group(1):
                    s3_url = match.group(1)
                    xds = rioxarray.open_rasterio(s3_url)
                    # Slice into `y` using slice(maxy, miny) because
                    # `y` will be high to low typically because origin = upper left corner
                    # Aimee(TODO): Check the assumption (origin = upper left corner)
                    ds = xds.sel(
                        x=slice(bounds[0], bounds[2]), y=slice(bounds[3], bounds[1])
                    )
                else:
                    match = re.search(
                        f"({self.titiler_endpoint}/mosaicjson/mosaics/.+)/tiles",
                        layer_url,
                    )
                    if match:
                        mosaic_url = match.groups()[0]
                        # From titiler docs http://titiler.maap-project.org/docs
                        # /mosaicjson/{minx},{miny},{maxx},{maxy}/assets
                        str_bounds = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}"
                        assets_endpoint = f"{self.titiler_endpoint}/mosaicjson/{str_bounds}/assets?url={mosaic_url}/mosaicjson"
                        # create a dataset from multiple COGs
                        assets_response = requests.get(assets_endpoint)
                        datasets = []
                        assets = assets_response.json()
                        ds = self.gen_mosaic_dataset_reader(assets, bounds)
                if ds.any():
                    ds.attrs["title"] = title
                    self.selected_data.append(ds)
        return self.selected_data
