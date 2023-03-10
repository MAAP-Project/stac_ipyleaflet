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
    # TODO(aimee): right now this is specific to MAAP but we should make it generic.
    titiler_endpoint: str = "https://titiler.maap-project.org"
    histogram_layer: Popup
    warning_layer: Popup = None 
    loading_widget_layer: Popup = None 
    bbox_centroid: list = []

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

        f=open("./loading.gif", "rb")
        gif_widget=ipywidgets.Image(
            value=f.read(),
            format='png',
            width=200,
            height=200,
        )

        loading_widget=ipywidgets.VBox()
        loading_widget.children=[gif_widget]
        loading_location = self.bbox_centroid or self.center
        self.loading_widget_layer = Popup(child=loading_widget, min_width=200, min_height=200)

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
                # src.part((minx, miny, maxx, maxy), **kwargs)
                return src.part(bounds, *args, **kwargs)
        # mosaic_reader will use multithreading to distribute the image fetching 
        # and then merge all arrays together
        # Vincent: This will not work if the image do not have the same resolution (because we won't be able to overlay them).
        # If you know the resolution you want to use you can use width=.., height=.. instead of max_size=512 (it will ensure you create the same array size for all the images.
        # change the max_size to make it faster/slower
        # TODO(aimee): make this configurable
        img, _ = mosaic_reader(assets, reader=_part_read, max_size=512)

        # create Masked Array from ImageData
        data = img.as_masked()
        # Avoid non-masked nan/inf values
        numpy.ma.fix_invalid(data, copy=False)
        # TODO(aimee): determine if this might help for creating the histograms quickly
        # hist = {}
        # for ii, b in enumerate(img.count):
        #     h_counts, h_keys = numpy.histogram(data[b].compressed())
        #     hist[f"b{ii + 1}"] = [h_counts.tolist(), h_keys.tolist()]        
        return xr.DataArray(data)

    def update_selected_data(self):
        layers = self.layers
        # TODO(aimee): if geometry hasn't changed and a previously selected layer is still selected, don't re-fetch it.
        self.selected_data = []
        visible_layers = [layer for layer in layers if type(layer) == TileLayer and layer.visible and not layer.base]
        geometries = [self.draw_control.last_draw['geometry']]
        if geometries[0]:
            box = Polygon(geometries[0]['coordinates'][0])
            # https://shapely.readthedocs.io/en/latest/reference/shapely.bounds.html?highlight=bounds#shapely.bounds
            # For geometries these 4 numbers are returned: min x, min y, max x, max y.
            bounds = box.bounds
            self.bbox_centroid = [box.centroid.y, box.centroid.x]

            if len(visible_layers) !=0:
                self.loading_widget_layer.location = self.bbox_centroid
                if self.loading_widget_layer not in self.layers:
                    self.add_layer(self.loading_widget_layer)
                else:
                    self.loading_widget_layer.open_popup()

            for idx, layer in enumerate(visible_layers):
                layer_url = layer.url
                ds = None
                title = layer.name.replace('_', ' ').upper()  
                match = re.search('url=(.+.tif)', layer_url)
                if match and match.group(1):
                    s3_url = match.group(1)
                    xds = rioxarray.open_rasterio(s3_url)
                    # Slice into `y` using slice(maxy, miny) because
                    # `y` will be high to low typically because origin = upper left corner
                    # Aimee(TODO): Check the assumption (origin = upper left corner)
                    ds = xds.sel(x=slice(bounds[0], bounds[2]), y=slice(bounds[3], bounds[1]))
                else:
                    match = re.search(f"({self.titiler_endpoint}/mosaicjson/mosaics/.+)/tiles", layer_url)
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

    def error_message(self, msg):
        out = ipywidgets.Output()
        with out:
            print(msg)
            self.gen_popup_icon(msg)
            display()
            return

    # TODO(aimee): if you try and create a histogram for more than one layer, it creates duplicates in the popup
    def create_histograms(self, b):
        if self.histogram_layer in self.layers:
            self.remove_layer(self.histogram_layer)
        # TODO(aimee): make this configurable
        minx, maxx = [0, 500]
        plot_args = {"range": (minx, maxx)}
        fig = plt.figure()
        hist_widget = ipywidgets.VBox()
        try:
            self.update_selected_data()
        except Exception as e:
            return self.error_message(e)
        if len(self.selected_data) == 0:
            return self.error_message("No data or bounding box selected.")
        else:
            for idx, dataset in enumerate(self.selected_data):
                axes = fig.add_subplot(int(f"22{idx+1}"))
                plot_args['ax'] = axes
                # create a histogram
                out = ipywidgets.Output()
                with out:
                    out.clear_output()
                    try:
                        dataset.plot.hist(**plot_args)
                    except Exception as err:
                        self.remove_layer(self.loading_widget_layer)
                        self.gen_popup_icon(f"Error: {err}")
                        return 
                    axes.set_title(dataset.attrs['title'])
                    display(fig)

        hist_widget.children = [out]
        hist_location = self.bbox_centroid or self.center
        histogram_layer = Popup(child=hist_widget, location=hist_location, min_width=500, min_height=300)
        self.histogram_layer = histogram_layer
        self.remove_layer(self.loading_widget_layer)
        self.add_layer(histogram_layer)
        return None

    def draw_biomass_map(self):
        self.add_biomass_layers()
        self.add_toolbar()
        return None

    # generates warning/error popup
    def gen_popup_icon(self, msg):
        warning_msg = HTML()
        warning_msg.value=f"<b>{msg}</b>"
        popup_warning = Popup(location=self.bbox_centroid or self.center, draggable=True, child=warning_msg)
        self.warning_layer=popup_warning
        self.add_layer(popup_warning);