"""Main module."""
import csv
from io import BytesIO
import json
import os
import re
import requests

from ipyleaflet import Map, DrawControl, WidgetControl, TileLayer, Popup
from IPython.display import display
import ipywidgets
import matplotlib.pyplot as plt
#from pydantic import BaseModel
from shapely.geometry import Polygon
import rioxarray
import xarray as xr
import numpy
from rio_tiler.io import Reader
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.models import ImageData

class StacIpyleaflet(Map):
    """
    Stac ipyleaflet is an extension to ipyleaflet `Map`.
    """
    draw_control: DrawControl
    titiler_url: str = "https://titiler.maap-project.org"

    def __init__(self, **kwargs):
        if "center" not in kwargs:
            kwargs["center"] = [20, 0]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 2

        # Create map
        super().__init__(**kwargs)

        # Add rectangle draw control for bounding box
        # TODO(aimee): can we remove the other draw controls?
        self.selected_data = []
        self.draw_control = None
        draw_control = DrawControl(
            edit=True,
            remove=True,
        )
        draw_control.rectangle = {
            "shapeOptions": {
                "fillColor": "transparent",
                "color": "#333",
                "fillOpacity": 1.0
            }
        }
        self.add_control(draw_control)
        self.draw_control = draw_control
        return None

    def layers_button_clicked(self, b):
        layers_widget = self.layers_widget
        if layers_widget.layout.display == 'none':
            layers_widget.layout.display = 'block'
        elif layers_widget.layout.display == 'block':
            layers_widget.layout.display = 'none'

    def add_layers_widget(self):
        # Adds a list of layers to toggle on and off via checkboxes
        layers_widget = ipywidgets.VBox()
        layers_hbox = []

        for layer in self.layers:
            layer_chk = ipywidgets.Checkbox(
                value=layer.visible,
                description=layer.name,
                indent=False
            )
            ipywidgets.jslink((layer_chk, "value"), (layer, "visible"))
            hbox = ipywidgets.HBox(
                [layer_chk]
            )
            layers_hbox.append(hbox)
        layers_widget.children = layers_hbox
        layers_widget.layout.display ='none'
        return layers_widget

    def add_toolbar(self):
        # Add a widget for the layers
        self.layers_widget = self.add_layers_widget()

        # Add a button to toggle the layers checkbox widget on and off
        layers_button = ipywidgets.Button(
            tooltip="Open Layers List",
            icon="map-o",
            layout=ipywidgets.Layout(height="28px", width="38px"),
        )

        layers_button.on_click(self.layers_button_clicked)

        hist_button = ipywidgets.Button(
            tooltip="Create histogram",
            icon="bar-chart",
            layout=ipywidgets.Layout(height="28px", width="38px"),
        )
        hist_button.on_click(self.create_histograms)
        toolbar_widget = ipywidgets.VBox()
        toolbar_widget.children = [layers_button, hist_button, self.layers_widget]
        toolbar_control = WidgetControl(widget=toolbar_widget, position="topright")
        self.add(toolbar_control)

    def add_biomass_layers(self):
        biomass_file = 'biomass-layers.csv'
        with open(biomass_file, newline='') as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None)  # skip the headers
            for row in csv_reader:
                name, tile_url = row[0], row[1]
                tile_layer = TileLayer(url=tile_url, attribution=name, name=name, visible=False)
                self.add_layer(tile_layer)

    def gen_mosaic_dataset_reader(selv, assets, bounds):
        # see https://github.com/cogeotiff/rio-tiler/blob/main/rio_tiler/io/rasterio.py#L368-L380
        def _part_read(src_path: str, *args, **kwargs) -> ImageData:
            with Reader(src_path) as src:
                return src.part(bounds, *args, **kwargs)
        # mosaic_reader will use multithreading to distribute the image fetching 
        # and them merge all arrays together
        img, _ = mosaic_reader(assets, reader=_part_read, max_size=512) # change the max_size to make it faster/slower 

        data = img.as_masked()  # create Masked Array from ImageData
        # Avoid non masked nan/inf values
        numpy.ma.fix_invalid(data, copy=False)
        return xr.DataArray(data)
    
    # TODO(aimee): compare performance, but right now this generates an error 
    # ValueError: Could not find any dimension coordinates to use to order the datasets for concatenation
    def gen_mosaic_dataset_crop(self, assets, str_bounds):
        datasets = []
        for asset in assets:
            try:
                crop_endpoint = f"{self.titiler_url}/cog/crop/{str_bounds}.npy?url={asset}&max_size=512"  # Same here you can either use max_size or width&height
                res = requests.get(crop_endpoint)
                arr = numpy.load(BytesIO(res.content))
                tile, mask = arr[0:-1], arr[-1]

                # TODO:
                # convert tile/mask to xarray dataset
                ds = xr.DataArray(tile)
                datasets.append(ds)
            except:
                pass

        ds = xr.combine_by_coords(datasets) #, fill_value=datasets[0]._FillValue)        

    def update_selected_data(self):
        layers = self.layers
        visible_layers = [layer for layer in layers if type(layer) == TileLayer and layer.visible and not layer.base]
        geometries = [self.draw_control.last_draw['geometry']]
        if geometries[0]:
            box = Polygon(geometries[0]['coordinates'][0])
            bounds = box.bounds
            for idx, layer in enumerate(visible_layers):
                layer_url = layer.url
                title = layer.name.replace('_', ' ').upper()  
                match = re.search('url=(.+.tif)', layer_url) 
                if match and match.group(1):
                    s3_url = match.group(1)
                    xds = rioxarray.open_rasterio(s3_url)
                    ds = xds.sel(x=slice(bounds[0], bounds[2]), y=slice(bounds[3], bounds[1]))
                else:
                    match = re.search('(https://.+)/tiles', layer_url)
                    if match:
                        mosaic_url = match.groups()[0]
                        str_bounds = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}"
                        assets_endpoint = f"{self.titiler_url}/mosaicjson/{str_bounds}/assets?url={mosaic_url}/mosaicjson"
                        # create a dataset from multiple COGs
                        assets_response = requests.get(assets_endpoint)
                        datasets = []
                        assets = assets_response.json()
                        ds1 = self.gen_mosaic_dataset_reader(assets, bounds)
                        #ds2 = self.gen_mosaic_dataset_crop(assets, str_bounds)
                ds1.attrs["title"] = title
                self.selected_data.append(ds1)
        return self.selected_data

    def create_histograms(self, b):
        print("in create histograms")
        minx, maxx = [0, 500]
        plot_args = {"range": (minx, maxx)}
        fig = plt.figure()
        hist_widget = ipywidgets.VBox()
        out = ipywidgets.Output()
        out.clear_output()
        selected_data = self.update_selected_data()
        if len(selected_data) == 0:
            with out:
                print("No data selected")
                display()
                return
        else:
            for idx, dataset in enumerate(selected_data):
                axes = fig.add_subplot(int(f"22{idx+1}"))
                plot_args['ax'] = axes
                # create a histogram
                with out:
                    dataset.plot.hist(**plot_args)
                    axes.set_title(dataset.attrs['title'])
                    display(fig)
        hist_widget.children = [out]
        histogram_layer = Popup(child=hist_widget, location=self.center, min_width=200, min_height=200)
        self.add_layer(histogram_layer)
        return None

    def draw_biomass_map(self):
        self.add_biomass_layers()
        self.add_toolbar()
        return None
