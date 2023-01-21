"""Main module."""
import csv
import functools
import json
import os
import re
import requests

from ipyleaflet import Map, DrawControl, WidgetControl, TileLayer
from IPython.display import display
import ipywidgets
import matplotlib.pyplot as plt
#from pydantic import BaseModel
from shapely.geometry import Polygon
import rioxarray
import xarray as xr

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
        self.draw_control = None
        draw_control = DrawControl(
            edit=True,
            remove=True,
        )
        draw_control.rectangle = {
            "shapeOptions": {
                "fillColor": "transparent",
                "color": "#fca45d",
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
            for row in csv_reader:
                name, tile_url = row[0], row[1]
                tile_layer = TileLayer(url=tile_url, attribution=name, name=name, visible=False)
                self.add_layer(tile_layer)

    # def create_histograms(self, b):
    #     b = ipywidgets.Button(description='(50% width, 80px height) button',
    #             layout=ipywidgets.Layout(width='50%', height='80px'))
    #     hist_widget = ipywidgets.VBox()
    #     hist_widget.children = [b]
    #     histogram_control = WidgetControl(widget=hist_widget, position="topright")
    #     self.add(histogram_control)
    def create_histograms(self, b):
        print("in create histograms")
        minx, maxx = [0, 500]
        plot_args = {"range": (minx, maxx)}
        layers = self.layers
        visible_layers = [layer for layer in layers if layer.visible and not layer.base]
        fig = plt.figure()
        geometries = [self.draw_control.last_draw['geometry']]
        if geometries[0]:
            box = Polygon(geometries[0]['coordinates'][0])
            bounds = box.bounds
            for idx, layer in enumerate(visible_layers):
                layer_url = layer.url
                title = layer.name.replace('_', ' ').upper()
                axes = fig.add_subplot(int(f"22{idx+1}"))
                match = re.search('url=(.+.tif)', layer_url)
                plot_args['ax'] = axes
                hist_widget = ipywidgets.VBox()
                out = ipywidgets.Output()
                # create a histogram from single COG
                if match and match.group(1):
                    s3_url = match.group(1)
                    xds = rioxarray.open_rasterio(s3_url)
                    ds = xds.sel(x=slice(bounds[0], bounds[2]), y=slice(bounds[3], bounds[1]))
                # create a histogram from mulitiple COGs via mosaicjson
                else:
                    match = re.search('(https://.+)/tiles', layer_url)
                    if match:
                        mosaic_url = match.groups()[0]
                        str_bounds = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}"
                        assets_endpoint = f"{self.titiler_url}/mosaicjson/{str_bounds}/assets?url={mosaic_url}/mosaicjson"
                        # create a dataset from multiple COGs?
                        assets_response = requests.get(assets_endpoint)
                        datasets = []
                        for asset in assets_response.json():
                            # TODO: try/catch here in case of Access Denied
                            xds = rioxarray.open_rasterio(asset)
                            # TODO: some datasets have y in reverse, is that true for all?
                            subset = xds.sel(x=slice(bounds[0], bounds[2]), y=slice(bounds[3], bounds[1]), band=1)
                            if subset.size > 0:
                                datasets.append(subset)
                        ds = xr.combine_by_coords(datasets, fill_value=datasets[0]._FillValue)
                    else:
                        (f"no files for for {layer}")
                with out:
                    if ds.any():
                        ds.plot.hist(**plot_args)
                        axes.set_title(title)
                        display(fig)
                    else:
                        display(f"<p>no files for for {layer}</p>")
            hist_widget.children = [out]
            histogram_control = WidgetControl(widget=hist_widget, position="bottomright")
            self.add(histogram_control)
            # else:
            #     hist_widget = ipywidgets.VBox()
            #     out = ipywidgets.Output()
            #     with out:
            #         display(f"<p>No layers selected</p>")
            #     hist_widget.children = [out]
            #     histogram_control = WidgetControl(widget=hist_widget, position="bottomright")
            #     self.add(histogram_control)
        return None

    def draw_biomass_map(self):
        self.add_biomass_layers()
        self.add_toolbar()
        return None
