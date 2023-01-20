"""Main module."""
import csv
import functools
import json
import os
import re
import requests

from ipyleaflet import Map, DrawControl, WidgetControl, TileLayer
import ipywidgets
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import rioxarray
import xarray as xr

def draw_basic_map():
    # Create map
    #default_layout=ipywidgets.Layout(width='100%', height='1200px')
    m = Map(center=(0, 0), zoom=4)#, layout=default_layout)
    
    # Add rectangle draw control for bounding box
    # TODO(aimee): can we remove the other draw controls?
    draw_control = DrawControl(
        edit=True,
        remove=True,
        circlemarker={'shapeOptions': {}},
        marker={'shapeOptions': {}},
        circle={'shapeOptions': {}},    
        polyline={'shapeOptions': {}},
        polygon = {'shapeOptions': {}}        
    )    
    draw_control.rectangle = {
        "shapeOptions": {
            "fillColor": "transparent",
            "color": "#fca45d",
            "fillOpacity": 1.0
        }
    }
    m.add_control(draw_control)
    return m, draw_control

def layers_button_clicked(b, layers_widget_=None):
    if layers_widget_.layout.display == 'none':
        layers_widget_.layout.display = 'block'
    elif layers_widget_.layout.display == 'block':
        layers_widget_.layout.display = 'none'

def add_layers_widget(m):
    # Adds a list of layers to toggle on and off via checkboxes   
    layers_widget = ipywidgets.VBox()
    layers_hbox = []
    
    for layer in m.layers:
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
    
def add_toolbar(m):
    # Add a widget for the layers
    layers_widget = add_layers_widget(m)

    # Add a button to toggle the layers checkbox widget on and off
    layers_button = ipywidgets.Button(
        tooltip="Open Layers List",
        icon="map-o",
        layout=ipywidgets.Layout(height="28px", width="38px"),
    )

    layers_button.on_click(functools.partial(layers_button_clicked, layers_widget_=layers_widget))

    hist_button = ipywidgets.Button(
        tooltip="Create histogram",
        icon="bar-chart",
        layout=ipywidgets.Layout(height="28px", width="38px"),
    )
    toolbar_widget = ipywidgets.VBox()
    toolbar_widget.children = [layers_button, hist_button, layers_widget]
    toolbar_control = WidgetControl(widget=toolbar_widget, position="topright")    
    m.add(toolbar_control)

def add_biomass_layers(m):
    biomass_file = 'biomass-layers.csv'
    with open(biomass_file, newline='') as f:
        csv_reader = csv.reader(f)  
        for row in csv_reader:
            name, tile_url = row[0], row[1]   
            tile_layer = TileLayer(url=tile_url, attribution=name, name=name, visible=False)
            m.add_layer(tile_layer)

def create_histograms(m, draw_control):
    minx, maxx = [0, 500]
    plot_args = {"range": (minx, maxx)}
    layers = m.layers
    visible_layers = [layer for layer in layers if layer.visible and not layer.base]
    fig = plt.figure()
    geometries = [draw_control.last_draw['geometry']]
    box = Polygon(geometries[0]['coordinates'][0])
    bounds = box.bounds    
    for idx, layer in enumerate(visible_layers):
        layer_url = layer.url
        title = layer.name.replace('_', ' ').upper()
        axes = fig.add_subplot(int(f"22{idx+1}"))        
        match = re.search('url=(.+.tif)', layer_url)
        plot_args['ax'] = axes
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
                assets_endpoint = f"{titiler_url}/mosaicjson/{str_bounds}/assets?url={mosaic_url}/mosaicjson"
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
        ds.plot.hist(**plot_args)
        axes.set_title(title)
            
def draw_biomass_map():
    m, draw_control = draw_basic_map()
    add_biomass_layers(m)
    add_toolbar(m)
    return m, draw_control
