"""Main module."""
from ipyleaflet import Map, Popup, TileLayer, WidgetControl
from IPython.display import display
from ipywidgets import Box, HBox, VBox, Layout, SelectionSlider, HTML, IntSlider, Image
from ipywidgets import Checkbox, Dropdown, Tab, ToggleButton, Button
from ipywidgets import HTML, Output, jslink
import logging
import matplotlib.pyplot as plt
from rio_tiler.io import Reader
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.models import ImageData
from shapely.geometry import Polygon
import xarray as xr

from stac_ipyleaflet.constants import (
    STAC_CATALOG,
    TITILER_STAC_ENDPOINT,
    TITILER_ENDPOINT,
)
from stac_ipyleaflet.stac_discovery.stac_widget import StacDiscoveryWidget
from stac_ipyleaflet.widgets.basemaps import BasemapsWidget
from stac_ipyleaflet.utilities.helpers import add_layers_options


class StacIpyleaflet(Map):
    histogram_layer: Popup
    warning_layer: Popup = None
    loading_widget_layer: Popup = None
    bbox_centroid: list = []

    titiler_stac_endpoint = TITILER_STAC_ENDPOINT

    def __init__(self, **kwargs):
        from stac_ipyleaflet.widgets.inspect import InspectControlWidget
        from stac_ipyleaflet.widgets.draw import DrawControlWidget

        if "center" not in kwargs:
            kwargs["center"] = [20, 0]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 4

        if "layout" not in kwargs:
            kwargs["layout"] = Layout(height="600px")

        if "scroll_wheel_zoom" not in kwargs:
            kwargs["scroll_wheel_zoom"] = True

        # Create map
        super().__init__(**kwargs)

        self.accent_color = "SteelBlue"
        self.layers = BasemapsWidget.template(self)

        self.buttons = {}
        self.selected_data = []
        self.histogram_layer = None
        self.draw_control_added = False
        self.point_control_added = False
        self.aoi_coordinates = []
        self.aoi_bbox = ()
        self.applied_layers = []
        self.inspect_widget = None
        self.marker_added = False

        self.create_buttons_layout()
        self.check_for_env_vars()
        self.add_default_layer_options()
        self.add_custom_tools()

        self.point_control = InspectControlWidget.template(self)
        self.draw_control = DrawControlWidget.template(self)
        return None

    def check_for_env_vars(self):
        missing = []
        warning_log = ""
        if TITILER_STAC_ENDPOINT is None:
            missing.append("TITILER_STAC_ENDPOINT")
            warning_log += (
                "os.environ['TITILER_STAC_ENDPOINT']='REPLACE_WITH_TITILER_STAC_URL'\n"
            )
        if TITILER_ENDPOINT is None:
            missing.append("TITILER_ENDPOINT")
            warning_log += "os.environ['TITILER_ENDPOINT']='REPLACE_WITH_TITILER_URL'\n"
        if STAC_CATALOG is None:
            missing.append("STAC_CATALOG")
            warning_log += "os.environ['STAC_CATALOG'] = {'name': 'REPLACE_WITH_STAC_CATALOG_NAME_FOR_LABEL_USE', 'url': 'REPLACE_WITH_STAC_CATALOG_URL'}\n"
        if len(missing) > 0:
            logging.warning(
                f"Following environment variable(s) are missing {missing} \n To set these environment variables, run this code: \n \n import os \n {warning_log}"
            )
        return

    def add_default_layer_options(self):
        if TITILER_ENDPOINT is not None and "maap" in TITILER_ENDPOINT:
            add_layers_options(self.add_layer, "biomass-layers.csv")
        return

    def create_buttons_layout(self):
        interact_btn = self.create_widget_button(
            buttonId="interact",
            toolTipMsg="Interact with the map",
            description="Interact",
            icon="pencil",
            onClick=self.toggle_interact_widget_display,
        )
        layers_btn = self.create_widget_button(
            buttonId="layers",
            toolTipMsg="Open/Close Layers Menu",
            description="Layers",
            icon="map-o",
            onClick=self.toggle_layers_widget_display,
        )
        stac_btn = self.create_widget_button(
            buttonId="stac",
            toolTipMsg="Open/Close STAC Data Search",
            description="STAC Data",
            icon="search",
            onClick=self.toggle_stac_widget_display,
        )

        buttons_box_layout = Layout(
            display="flex",
            flex_flow="row",
            align_items="center",
            justify_content="center",
            width="100%",
            height="50px",
        )
        buttons_box = HBox(
            children=[interact_btn, layers_btn, stac_btn],
            layout=buttons_box_layout,
        )
        display(buttons_box)
        return buttons_box

    def create_widget_button(self, **kwargs):
        main_button_layout = Layout(
            width="120px", height="35px", border="1px solid #4682B4"
        )
        btn = ToggleButton(
            description=kwargs["description"],
            icon=kwargs["icon"],
            layout=main_button_layout,
        )
        btn.style.text_color = self.accent_color
        btn.style.button_color = "transparent"
        btn.tooltip = kwargs["toolTipMsg"]
        btn.observe(kwargs["onClick"], type="change", names=["value"])
        btn_id = kwargs["buttonId"]
        self.buttons[btn_id] = btn
        return btn

    def create_widget_tab(self, **kwargs):
        desc = HTML(
            value=f"<h4>{kwargs['desc']}</h4>",
        )
        data_value = HTML(
            value=f"<code>{kwargs['emptyValueState']}</code>",
            description="",
        )

        button = Button(
            description=kwargs["btnDesc"],
            tooltip=kwargs["btnDesc"],
            icon="trash",
            disabled=True,
        )

        item = HBox(
            [
                desc,
                data_value,
                button,
            ]
        )

        item.layout.flex_flow = "column"
        return item

    def remove_draw_controls(self):
        if self.draw_control_added:
            self.remove(self.draw_control)
            self.draw_control_added = False
        if self.point_control_added:
            self.remove(self.point_control)
            self.point_control_added = False
        return self

    # logic to handle main menu toggle buttons
    def toggle_layers_widget_display(self, b):
        if b["new"]:
            if self.layers_widget.layout.display == "none":
                self.layers_widget.layout.display = "block"
                self.stac_widget.layout.display = "none"
                self.interact_widget.layout.display = "none"
                self.buttons["stac"].value = False
                self.buttons["interact"].value = False
                self.remove_draw_controls()
        if not b["new"]:
            if self.layers_widget.layout.display == "block":
                self.layers_widget.layout.display = "none"

    def toggle_stac_widget_display(self, b):
        if b["new"]:
            if self.stac_widget.layout.display == "none":
                self.stac_widget.layout.display = "block"
                self.layers_widget.layout.display = "none"
                self.interact_widget.layout.display = "none"
                self.buttons["layers"].value = False
                self.buttons["interact"].value = False
                self.remove_draw_controls
        if not b["new"]:
            if self.stac_widget.layout.display == "block":
                self.stac_widget.layout.display = "none"

    def toggle_interact_widget_display(self, b):
        if b["new"]:
            if self.interact_widget.layout.display == "none":
                self.interact_widget.layout.display = "block"
                self.stac_widget.layout.display = "none"
                self.layers_widget.layout.display = "none"
                self.buttons["stac"].value = False
                self.buttons["layers"].value = False
                selected_tab = self.interact_widget.children[0].titles[
                    self.interact_widget.children[0].selected_index
                ]
                if selected_tab == "Point":
                    self.add_control(self.point_control)
                    self.point_control_added = True
                elif selected_tab == "Area":
                    self.add_control(self.draw_control)
                    self.draw_control_added = True
        if not b["new"]:
            if self.interact_widget.layout.display == "block":
                self.interact_widget.layout.display = "none"
                self.remove_draw_controls()

    @staticmethod
    def create_widget_layout():
        widget = Box(style={"max-width: 420px"})
        widget.layout.flex_flow = "column"
        widget.layout.max_height = "360px"
        widget.layout.overflow = "auto"
        return widget

    def create_interact_widget(self):
        interact_widget = self.create_widget_layout()

        tab_headers = ["Point", "Area"]
        tab_children = []
        tab_widget = Tab()

        out = Output()
        display(out)

        def toggle_interact_tab_change(event):
            selected_tab = self.interact_widget.children[0].titles[
                event.owner.selected_index
            ]
            if selected_tab == "Point":  # Inspect Control
                if self.draw_control_added:
                    self.remove(self.draw_control)
                    self.draw_control_added = False
                self.add_control(self.point_control)
                self.point_control_added = True
            elif selected_tab == "Area":  # Draw Control
                if self.point_control_added:
                    self.remove(self.point_control)
                    self.point_control_added = False
                self.add_control(self.draw_control)
                self.draw_control_added = True

        for tab in tab_headers:
            tab_content = VBox()
            if tab == "Point":
                hbox = self.create_widget_tab(
                    desc="Marker",
                    emptyValueState="Waiting for points of interest...",
                    btnDesc="Clear Markers",
                )
                tab_content.children = [VBox([hbox])]
                tab_children.append(tab_content)
            elif tab == "Area":
                hbox = self.create_widget_tab(
                    desc="Polygon",
                    emptyValueState="Waiting for area of interest...",
                    btnDesc="Clear AOI Polygon",
                )
                tab_content.children = [VBox([hbox])]
                tab_children.append(tab_content)
        tab_widget.children = tab_children
        tab_widget.titles = tab_headers
        interact_widget.children = [tab_widget]
        interact_widget.layout.display = "none"
        tab_widget.observe(toggle_interact_tab_change, names="selected_index")
        return interact_widget

    # @NOTE: Possibly move into its own child class file
    def create_layers_widget(self):
        layers_widget = self.create_widget_layout()

        tab_headers = ["Biomass Layers", "Basemaps"]
        tab_children = []
        tab_widget = Tab()

        out = Output()
        display(out)

        opacity_values = [i * 10 for i in range(10 + 1)]  # [0.001, 0.002, ...]

        def layer_checkbox_changed(change):
            layer = next(
                (x for x in self.layers if x.name == change.owner.description), None
            )
            if change.owner.value:
                self.applied_layers.append(layer)
            if not change.owner.value:
                self.applied_layers.remove(layer)

        def handle_basemap_opacity_change(change):
            selected_bm = self.basemap_selection_dd.value
            for l in self.layers:
                if l.base:
                    if l.name == selected_bm:
                        l.opacity = change["new"] / 100

        def handle_layer_opacity_change(change):
            selected_layer = change.owner.description
            if selected_layer not in self.applied_layers:
                return
            for l in self.layers:
                if l.name == selected_layer:
                    l.opacity = change["new"]

        for tab in tab_headers:
            tab_content = VBox()
            listed_layers = []
            # sort layers by name property
            layers_in_drawing_order = [l for l in self.layers]
            layerlist_layers = sorted(
                layers_in_drawing_order, key=lambda x: x.name, reverse=False
            )
            if tab == "Biomass Layers":
                layers_hbox = []
                for layer in layerlist_layers:
                    # check if layer name is a basemap
                    if not layer.base:
                        layer_checkbox = Checkbox(
                            value=layer.visible, description=layer.name, indent=False
                        )
                        jslink((layer_checkbox, "value"), (layer, "visible"))
                        layer_checkbox.observe(
                            layer_checkbox_changed, names="value", type="change"
                        )
                        hbox = HBox([layer_checkbox])
                        layer_opacity_slider = SelectionSlider(
                            value=1,
                            options=[("%g" % i, i / 100) for i in opacity_values],
                            description=layer.name,
                            continuous_update=False,
                            orientation="horizontal",
                            layout=Layout(margin="-12px 0 4px 0"),
                        )
                        layer_opacity_slider.style.description_width = "0px"
                        layer_opacity_slider.style.handle_color = self.accent_color
                        layer_opacity_slider.observe(
                            handle_layer_opacity_change, names="value"
                        )
                        layers_hbox.append(hbox)
                        layers_hbox.append(layer_opacity_slider)
                        listed_layers.append(layer.name)
                tab_content.children = [VBox(layers_hbox)]
                tab_children.append(tab_content)
            elif tab == "Basemaps":
                basemaps = []
                for layer in layerlist_layers:
                    # check if layer is a basemap
                    if layer.base:
                        basemaps.append((f"{layer.name}", f"{layer.name}"))

                def on_change(change):
                    if change["type"] == "change" and change["name"] == "value":
                        with out:
                            out.clear_output()
                            # print("changed to %s" % change['new'])
                            for l in self.layers:
                                if l.base:
                                    if l.name == change["new"]:
                                        l.opacity = basemap_opacity_slider.value / 100
                                        l.visible = True
                                    else:
                                        l.visible = False
                            return None

                dropdown = Dropdown(options=basemaps, value="Open Street Map")
                self.basemap_selection_dd = dropdown
                dropdown.observe(on_change)

                basemap_opacity_slider = IntSlider(
                    value=100,
                    min=0,
                    max=100,
                    step=10,
                    description="% Opacity:",
                    # disabled=False,
                    style={"bar_color": "maroon"},
                    continuous_update=False,
                    orientation="horizontal",
                    readout=True,
                    readout_format="d",
                )

                basemap_opacity_slider.style.handle_color = self.accent_color
                basemap_opacity_slider.observe(
                    handle_basemap_opacity_change, names="value"
                )
                tab_content.children = [dropdown, basemap_opacity_slider]
                tab_children.append(tab_content)

        tab_widget.children = tab_children
        tab_widget.titles = tab_headers
        print(tab_widget.box_style)
        layers_widget.children = [tab_widget]
        layers_widget.layout.display = "none"
        return layers_widget

    def add_custom_tools(self):
        # Create custom map widgets
        self.layers_widget = self.create_layers_widget()
        self.stac_widget = StacDiscoveryWidget.template(self)
        self.interact_widget = self.create_interact_widget()

        layers_widget = VBox([self.layers_widget])
        stac_widget = VBox([self.stac_widget])
        interact_widget = VBox([self.interact_widget])

        layers_control = WidgetControl(
            widget=layers_widget, position="topright", id="layers_widget"
        )
        stack_control = WidgetControl(
            widget=stac_widget, position="topright", id="stac_widget"
        )
        interact_control = WidgetControl(
            widget=interact_widget, position="topright", id="interact_widget"
        )

        self.add(layers_control)
        self.add(stack_control)
        self.add(interact_control)

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
            return tile_layer

        except Exception as e:
            logging.error("Failed to add the specified TileLayer.")
            raise Exception(e)

    """ def gen_mosaic_dataset_reader(self, assets, bounds):
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
        return xr.DataArray(data) """

    """ def update_selected_data(self):
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

            for layer in visible_layers:
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
                    uuid_pattern = r'([a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12})'
                    match = re.search(f"({titiler_endpoint}/mosaics/{uuid_pattern})/tiles", layer_url)
                    if match:
                        mosaic_url = match.groups()[0]
                        # From titiler docs http://titiler.maap-project.org/docs
                        # /{minx},{miny},{maxx},{maxy}/assets
                        str_bounds = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}"
                        assets_endpoint = f"{self.titiler_stac_endpoint}/mosaicjson/{str_bounds}/assets?url={mosaic_url}/mosaicjson"
                        # create a dataset from multiple COGs
                        assets_response = requests.get(assets_endpoint)
                        if assets_response.status_code == 200:
                            assets = assets_response.json()
                            ds = self.gen_mosaic_dataset_reader(assets, bounds)
                if ds.any():
                    ds.attrs["title"] = title
                    self.selected_data.append(ds)
        return self.selected_data """

    """ def error_message(self, msg):
        out = Output()
        with out:
            print(msg)
            self.gen_popup_icon(msg)
            display()
            return """

    # TODO(aimee): if you try and create a histogram for more than one layer, it creates duplicates in the popup
    """ def create_histograms(self, b):
        print(self, b)
        if self.histogram_layer in self.layers:
            self.remove_layer(self.histogram_layer)
        # TODO(aimee): make this configurable
        minx, maxx = [0, 500]
        plot_args = {"range": (minx, maxx)}
        fig = plt.figure()
        hist_widget = VBox()
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
                out = Output()
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
        return None """

    # generates warning/error popup
    """ def gen_popup_icon(self, msg):
        warning_msg = HTML()
        warning_msg.value=f"<b>{msg}</b>"
        popup_warning = Popup(location=self.bbox_centroid or self.center, draggable=True, child=warning_msg)
        self.warning_layer=popup_warning
        self.add_layer(popup_warning) """
