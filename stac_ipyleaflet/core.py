"""Main module."""
import csv
from io import BytesIO
import re
import requests

from ipyleaflet import Map, DrawControl, WidgetControl, TileLayer, Popup
from .stac_discovery.stac_widget import StacDiscoveryWidget
from IPython.display import display
import ipywidgets
from ipywidgets import HTML
import matplotlib.pyplot as plt
#from pydantic import BaseModel
from shapely.geometry import Polygon
import rioxarray
import xarray as xr
import numpy
import numpy.ma as ma
from rio_tiler.io import Reader
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.models import ImageData

class StacIpyleaflet(Map):
    """
    Stac ipyleaflet is an extension to ipyleaflet `Map`.
    """
    draw_control: DrawControl
    titiler_url: str = "https://titiler.maap-project.org"
    histogram_layer: Popup
    warning_layer: Popup = None 

    def __init__(self, **kwargs):
        if "center" not in kwargs:
            kwargs["center"] = [20, 0]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 2

        # Create map
        super().__init__(**kwargs)

        # Add rectangle draw control for bounding box
        # TODO(aimee): Remove the other draw controls
        self.selected_data = []
        self.draw_control = None
        self.histogram_layer = None
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
    
    def stac_widget_display(self, b):
        stac_widget = self.stac_widget
        if stac_widget.layout.display == 'none':
            stac_widget.layout.display = 'block'
        elif stac_widget.layout.display == 'block':
            stac_widget.layout.display = 'none'

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
        self.stac_widget = StacDiscoveryWidget.template(self)

        # Add a button to toggle the layers checkbox widget on and off
        stac_widget_button = ipywidgets.Button(
            tooltip="STAC Discovery",
            icon="stack-exchange",
            layout=ipywidgets.Layout(height="28px", width="38px"),
        )
        stac_widget_button.on_click(self.stac_widget_display)

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

        stac_widget = ipywidgets.VBox()
        stac_widget.children = [stac_widget_button, self.stac_widget]
        self.add(WidgetControl(widget=stac_widget, position="topright"))

    def add_biomass_layers(self):
        biomass_file = 'biomass-layers.csv'
        with open(biomass_file, newline='') as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None)  # skip the headers
            for row in csv_reader:
                name, tile_url = row[0], row[1]
                tile_layer = TileLayer(url=tile_url, attribution=name, name=name, visible=False)
                self.add_layer(tile_layer)

    def find_layer(self, name: str):
        layers = self.layers

        for layer in layers:
            if layer.name == name:
                return layer
        return None

    def add_layer(self, layer):
        existing_layer = self.find_layer(layer.name)
        if existing_layer is not None:
            self.remove_layer(existing_layer)
        super().add_layer(layer)

    def add_tile_layer(
        self,
        url,
        name,
        attribution,
        opacity=1.0,
        shown=True,
        **kwargs,
    ):
        """Adds a TileLayer to the map.
        Args:
            url (str): The URL of the tile layer.
            name (str): The layer name to use for the layer.
            attribution (str): The attribution to use.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """
        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 100
        if "max_native_zoom" not in kwargs:
            kwargs["max_native_zoom"] = 100
        try:
            tile_layer = TileLayer(
                url=url,
                name=name,
                attribution=attribution,
                opacity=opacity,
                visible=shown,
                **kwargs,
            )
            self.add_layer(tile_layer)

        except Exception as e:
            print("Failed to add the specified TileLayer.")
            raise Exception(e)

    def gen_mosaic_dataset_reader(self, assets, bounds):
        # see https://github.com/cogeotiff/rio-tiler/blob/main/rio_tiler/io/rasterio.py#L368-L380
        def _part_read(src_path: str, *args, **kwargs) -> ImageData:
            with Reader(src_path) as src:
                return src.part(bounds, *args, **kwargs)
        # mosaic_reader will use multithreading to distribute the image fetching 
        # and then merge all arrays together
        # Vincent: This will not work if the image do not have the same resolution (because we won't be able to overlay them). if you know the resolution you want to use you can use width=.., height=.. instead of max_size=512 (it will ensure you create the same array size for all the images.
        # change the max_size to make it faster/slower
        # TODO(aimee): make this configurable
        img, _ = mosaic_reader(assets, reader=_part_read, max_size=512)

        data = img.as_masked()  # create Masked Array from ImageData
        # Avoid non masked nan/inf values
        numpy.ma.fix_invalid(data, copy=False)
        # TODO(aimee): determine if this might help for creating the histograms quickly
        # hist = {}
        # for ii, b in enumerate(img.count):
        #     h_counts, h_keys = numpy.histogram(data[b].compressed())
        #     hist[f"b{ii + 1}"] = [h_counts.tolist(), h_keys.tolist()]        
        return xr.DataArray(data)
    
    # This is an alternative to the gen_mosaic_dataset_reader   
    def gen_mosaic_dataset_crop(self, assets, str_bounds):
        datasets = []
        for asset in assets:
            # get fill value
            asset_endpoint = f"{self.titiler_url}/cog/info?url={asset}"
            res = requests.get(asset_endpoint)
            no_data = res.json()['nodata_value']
            
            # TODO(aimee): make max_size configurable
            crop_endpoint = f"{self.titiler_url}/cog/crop/{str_bounds}.npy?url={asset}&max_size=512"  # Same here you can either use max_size or width & height
            res = requests.get(crop_endpoint)
            arr = numpy.load(BytesIO(res.content))
            tile, mask = arr[0:-1], arr[-1]
            ds = ma.masked_values(tile, int(no_data))
            if ds.any() == True:
                ds = xr.DataArray(tile)
                datasets.append(ds)
        # TODO(aimee): this will probably error if there is more than 1 dataset, since there are no coordinates set, so we need to figure how to combine these datasets
        return xr.combine_by_coords(datasets)      

    def update_selected_data(self):
        layers = self.layers
        # TODO(aimee): if geometry hasn't changed and a previously selected layer is still selected, don't re-fetch it.
        self.selected_data = []
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
                        ds = self.gen_mosaic_dataset_reader(assets, bounds)
                ds.attrs["title"] = title
                self.selected_data.append(ds)
        return self.selected_data

    # TODO(aimee): if you try and create a histogram for more than one layer, it creates duplicates in the popup
    def create_histograms(self, b):
        if self.histogram_layer:
            self.remove_layer(self.histogram_layer)
        # TODO(aimee): make this configurable
        minx, maxx = [0, 500]
        plot_args = {"range": (minx, maxx)}
        fig = plt.figure()
        hist_widget = ipywidgets.VBox()
        out = ipywidgets.Output()
        self.update_selected_data()
        if len(self.selected_data) == 0:
            with out:
                print("No data selected")
                if self.warning_layer:
                    self.remove_layer(self.warning_layer)
                
                warning_msg = HTML()
                warning_msg.value="<b>No data selected!</b>"
                popup_warning = Popup(location=[20, 0], draggable=True, child=warning_msg)
                self.warning_layer=popup_warning
                self.add_layer(popup_warning);
                display()
                return
        else:
            for idx, dataset in enumerate(self.selected_data):
                axes = fig.add_subplot(int(f"22{idx+1}"))
                plot_args['ax'] = axes
                # create a histogram
                with out:
                    out.clear_output()
                    dataset.plot.hist(**plot_args)
                    axes.set_title(dataset.attrs['title'])
                    display(fig)
        hist_widget.children = [out]
        histogram_layer = Popup(child=hist_widget, location=self.center, min_width=500, min_height=300)
        self.hisogram_layer = histogram_layer
        self.add_layer(histogram_layer)
        return None

    def draw_biomass_map(self):
        self.add_biomass_layers()
        self.add_toolbar()
        return None
