from ipyleaflet import Map, DrawControl, WidgetControl, TileLayer, Popup
from .stac_discovery.stac_widget import StacDiscoveryWidget
from .biomass_layers.biomass_widget import BiomassLayersWidget
from IPython.display import display

from ipywidgets import (
    Button,
    Checkbox,
    HBox,
    HTML,
    Image,
    jslink,
    Layout,
    Output,
    VBox,
)
#from pydantic import BaseModel
from typing import Optional

class StacIpyleaflet(Map):
    """Stac ipyleaflet is an extension to ipyleaflet `Map`."""
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
        gif_widget=Image(
            value=f.read(),
            format='png',
            width=200,
            height=200,
        )

        loading_widget=VBox()
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

    def add_toolbar(self):
        # Add a widget for the layers
        self.layers_widget = self.add_layers_widget()
        self.stac_widget = StacDiscoveryWidget.template(self)

        # Add a button to toggle the layers checkbox widget on and off
        stac_widget_button = Button(
            tooltip="STAC Discovery",
            icon="stack-exchange",
            layout=Layout(height="28px", width="38px"),
        )
        stac_widget_button.on_click(self.stac_widget_display)

        layers_button = Button(
            tooltip="Open Layers List",
            icon="map-o",
            layout=Layout(height="28px", width="38px"),
        )

        layers_button.on_click(self.layers_button_clicked)

        hist_button = Button(
            tooltip="Create histogram",
            icon="bar-chart",
            layout=Layout(height="28px", width="38px"),
        )

        def histogram_on_click(b):
            BiomassLayersWidget.create_histograms(self, b)

        hist_button.on_click(histogram_on_click)
        toolbar_widget = VBox()
        toolbar_widget.children = [layers_button, hist_button, self.layers_widget]
        toolbar_control = WidgetControl(widget=toolbar_widget, position="topright")
        self.add(toolbar_control)

        stac_widget = VBox()
        stac_widget.children = [stac_widget_button, self.stac_widget]
        self.add(WidgetControl(widget=stac_widget, position="topright"))

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
    
    # def add_layer_to_group(self, LayerGroup, layer):


    def add_tile_layer(
        self,
        url: str,
        name: str,
        attribution: str,
        opacity: Optional[float] = 1.0,
        shown: Optional[bool] = True,
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

    def error_message(self, msg):
        out = Output()
        with out:
            print(msg)
            self.gen_popup_icon(msg)
            display()
            return

    def draw_biomass_map(self):
        BiomassLayersWidget.add_biomass_layers(self)
        self.add_toolbar()
        return None

    # generates warning/error popup
    def gen_popup_icon(self, msg):
        warning_msg = HTML()
        warning_msg.value=f"<b>{msg}</b>"
        popup_warning = Popup(location=self.bbox_centroid or self.center, draggable=True, child=warning_msg)
        self.warning_layer=popup_warning
        self.add_layer(popup_warning)
    
    def add_layers_widget(self):
        # Adds a list of layers to toggle on and off via checkboxes
        layers_widget = VBox()
        layers_hbox = []

        for layer in self.layers:
            layer_chk = Checkbox(
                value=layer.visible,
                description=layer.name,
                indent=False
            )
            jslink((layer_chk, "value"), (layer, "visible"))
            hbox = HBox(
                [layer_chk]
            )
            layers_hbox.append(hbox)
        layers_widget.children = layers_hbox
        layers_widget.layout.display ='none'
        return layers_widget
