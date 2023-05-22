from datetime import datetime
from ipywidgets import Box, Combobox, DatePicker, Dropdown, HBox, HTML
from ipywidgets import Layout, Output, RadioButtons, Tab, ToggleButtons, VBox
from pystac_client import Client
from stac_ipyleaflet.stac_discovery.stac import Stac

class StacDiscoveryWidget():
    def template(self) -> Box( style={"max_height: 200px"}):
        titiler_stac_endpoint = "https://titiler.maap-project.org"
        standard_width = "440px"
        styles = {
            "init": {"description_width": "initial",},
            "desc": "white-space:normal;font-size:smaller; max-height:80px;"
        }
        layouts = {
            "default": Layout(width=standard_width, padding="2px 6px"),
            "header": Layout(width=standard_width, padding="2px 6px", margin="2px 2px -6px 2px"),
            "buttons": Layout(display="flex", flex_flow="row", justify_content="flex-end", margin="0.5rem 1.5rem"),
            "radio": Layout(display="flex", width="max-content", padding="2px 6px"),
        }

        output = Output(
            layout=Layout(width=standard_width, height="200px", padding="4px 8px 4px 8px", overflow="auto")
        )

        # Templates for the STAC Discovery Widget
        stac_widget = VBox()
        stac_widget.layout.width="480px"
        stac_widget.layout.height="400px"
        stac_widget.layout.flex_flow="column"
        stac_widget.layout.overflow="auto"

        stac_catalogs = [
            {"name": "MAAP STAC", "url": "https://stac.maap-project.org"},
            # {"name": "VEDA STAC", "url": "https://staging-stac.delta-backend.com"},
            # {"name": "MAAP STAC", "url": "https://wssn144yw1.execute-api.us-west-2.amazonaws.com/"},            
            {"name": "Element84 Earth Search", "url": "https://earth-search.aws.element84.com/v1"},
            # {"name": "Microsoft Planetary Computer", "url": "https://planetarycomputer.microsoft.com/api/stac/v1"},
        ]
        # make list of name values from stac_catalogs
        catalog_options = sorted([c['name'] for c in stac_catalogs])
        selected_catalog = stac_catalogs[0]
        for cat in stac_catalogs:
            # print(cat)
            stac_client = Client.open(cat["url"], headers=[])
            collections_object = stac_client.get_all_collections()
            collections = Stac.organize_collections(collections_object)
            cat["collections"] = collections
        if "collections" not in selected_catalog:
            print("COLLECTIONS NOT FOUND")
            return
        # else:
        selected_collection_options = sorted([c for c in selected_catalog["collections"]], key=lambda c: c["id"])
        selected_collection = selected_collection_options[0]
        self.stac_data = { 
            "catalog": selected_catalog,
            "collection": selected_collection,
            "items": []           
        }

        # STAC Widget Items
        catalogs_dropdown = Dropdown(
            options=catalog_options,
            value=self.stac_data["catalog"]["name"],
            style=styles["init"],
            disabled=True,
            layout=layouts["default"],
        )
        catalogs_box = VBox(
            [
                HTML(value="<b>Catalog</b>", style=styles["init"], layout=layouts["header"],),
                catalogs_dropdown
            ]
        )

        collections_dropdown = Dropdown(
            options=[c["id"] for c in selected_collection_options],
            value=self.stac_data["collection"]["id"],
            style=styles["init"],
            layout=layouts["default"],
        )
        collections_box = VBox(
            [
                HTML(value="<b>Collection</b>", style=styles["init"], layout=layouts["header"],),
                collections_dropdown
            ]
        )
        collection_description = HTML(
            value=f'<div style="{styles["desc"]}">{self.stac_data["collection"]["description"]}</div>',
            style=styles["init"],
            layout=layouts["default"],
        )
        collection_description_box = VBox(
            [
                HTML(value="<b>Description</b>", style=styles["init"], layout=layouts["header"],),
                collection_description
            ]
        )
        collection_url = HTML(
            value=f'<a href={self.stac_data["collection"]["href"]} target="_blank">{self.stac_data["collection"]["href"]}</a>',
            style=styles["init"],
            layout=layouts["default"],
        )
        stac_browser_url = self.stac_data["collection"]["href"].replace("https://", "https://stac-browser.maap-project.org/external/")
        stac_browser_url = self.stac_data["collection"]["href"].replace("https://", "https://stac-browser.maap-project.org/external/")
        collection_url_browser = HTML(
            value=f'<a href={stac_browser_url} target="_blank"><b>View in STAC Browser</b></a>',
            value=f'<a href={stac_browser_url} target="_blank"><b>View in STAC Browser</b></a>',
            style=styles["init"],
            layout=layouts["default"],
        )
        collection_url.style.text_color = "blue"
        collection_url_browser.style.text_color = "blue"
        collection_url_browser.style.text_color = "blue"
        collection_url_box = VBox(
            [
                HTML(value="<b>URL</b>", style=styles["init"], layout=layouts["header"],),
                collection_url, collection_url_browser
            ]
        )
        collection_start_date = DatePicker(
            value=datetime.strptime(self.stac_data["collection"]["start_date"], "%Y-%m-%d"),
            description="Start",
            disabled=False if collections_dropdown.value else True,
            style=styles["init"],
            layout=layouts["default"],
        )
        collection_end_date = DatePicker(
            value=datetime.strptime(self.stac_data["collection"]["end_date"], "%Y-%m-%d"),
            description="End",
            disabled=False if collections_dropdown.value else True,
            style=styles["init"],
            layout=layouts["default"],
        )
        collection_dates_box = VBox(
            [
                HTML(value="<b>Date Range</b>", style=styles["init"], layout=layouts["header"],),
                HBox([collection_start_date, collection_end_date])
            ]
        )
        items_dropdown = Dropdown(
            options=[],
            value=None,
            style=styles["init"],
            layout=layouts["default"]
        )
        items_box = VBox(
            [
                HTML(value="<b>Items</b>", style=styles["init"], layout=layouts["header"],),
                items_dropdown
            ]
        )
        # layer_name = Text(
        #     value="STAC Layer",
        #     description="Layer name:",
        #     tooltip="Enter a layer name for the selected file",
        #     style=styles["init"],
        #     layout=layouts["default"],
        # )

        band_width = "125px"

        singular_band_dropdown = Dropdown(
            options=[1],
            tooltip="Present Band",
            style=styles["init"],
            layout=layouts["default"],
        )

        singular_band_dropdown_box = VBox(
            [
                HTML(value="<b>Band(s)</b>", style=styles["init"], layout=layouts["header"],),
                singular_band_dropdown
            ]
        )

        vmin = HTML(
            value=None,
            description="vmin:",
            tooltip="Minimum value of the raster to visualize",
            style=styles["init"],
            layout=Layout(width=band_width, padding="4px 8px"),
        )
        vmax = HTML(
            value=None,
            description="vmax:",
            tooltip="Maximum value of the raster to visualize",
            style=styles["init"],
            layout=Layout(width=band_width, padding="4px 8px"),
        )
        nodata = HTML(
            value=None,
            description="Nodata:",
            tooltip="Nodata the raster to visualize",
            style=styles["init"],
            layout=Layout(width=band_width, padding="4px 8px"),
        )

        cmaps = [('Perceptually Uniform Sequential', [
                'viridis', 'plasma', 'inferno', 'magma', 'cividis']),
            ('Sequential', [
                'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']),
            ('Sequential (2)', [
                'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
                'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
                'hot', 'afmhot', 'gist_heat', 'copper']),
            ('Diverging', [
                'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']),
            ('Cyclic', ['twilight', 'twilight_shifted', 'hsv']),
            ('Qualitative', [
                'Pastel1', 'Pastel2', 'Paired', 'Accent',
                'Dark2', 'Set1', 'Set2', 'Set3',
                'tab10', 'tab20', 'tab20b', 'tab20c']),
            ('Miscellaneous', [
                'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern',
                'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg',
                'gist_rainbow', 'rainbow', 'jet', 'turbo', 'nipy_spectral',
                'gist_ncar'])]
        
        def list_palettes(add_extra=False, lowercase=False, category=""):
            """List all available colormaps. See a complete lost of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.
            Returns:
                list: The list of colormap names.
            """
            import matplotlib.pyplot as plt

            if not category == "":
                all_colormap_options = plt.colormaps()
                filtered_color_options = list(filter(lambda x: x[0].startswith(category), cmaps))
                palette_options = list(map(lambda x: x[1], filtered_color_options))[0]
                if add_extra:
                    palette_options += ["dem", "ndvi", "ndwi"]
                if lowercase:
                    palette_options = [i.lower() for i in palette_options]
                palette_options.sort()
                return palette_options
        
        def list_palette_categories():                        
            palette_categories = list(map(lambda x: x[0], cmaps))
            return palette_categories


        palette_category_options = list_palette_categories()
        palette_categories_dropdown = Dropdown(
            options=palette_category_options,
            value=palette_category_options[0],
            layout=layouts["default"],
            style=styles["init"],
        )        
        palette_categories_dropdown_box = VBox(
            [
                HTML(value="<b>Palette Category</b>", style=styles["init"], layout=layouts["header"],),
                palette_categories_dropdown
            ]
        )
        palette_options = list_palettes(lowercase=True, category=palette_categories_dropdown.value)
        # palettes_dropdown = Dropdown(
        #     options=palette_options,
        #     value=palette_options[0],
        #     description="Palette:",
        #     layout=layouts["default"],
        #     style=styles["init"],
        # )
        palette_radiobuttons = RadioButtons(
            options=palette_options,
            value=palette_options[0],
            layout=layouts["radio"],
            style=styles["init"],
        )
        palettes_radiobuttons_box = VBox(
            [
                HTML(value="<b>Palette</b>", style=styles["init"], layout=layouts["header"],),
                palette_radiobuttons
            ]
        )
        # TODO: Add STAC layers to LayerGroup instead of base
        # TODO: Add LayerGroup control to utilize STAC LayerGroup
        # TODO: Add back in Checkbox for layer name and additional visual parameters
        # checkbox = Checkbox(
        #     value=False,
        #     description="Additional params",
        #     indent=False,
        #     layout=layouts["default"],
        #     style=styles["init"],
        # )
        # add_params_text = "Additional parameters in the format of a dictionary, for example, \n {'palette': ['#006633', '#E5FFCC', '#662A00', '#D8D8D8', '#F5F5F5'], 'expression': '(SR_B5-SR_B4)/(SR_B5+SR_B4)'}"
        # add_params = Textarea(
        #     value="",
        #     placeholder=add_params_text,
        #     layout=layouts["default"],
        #     style=styles["init"],
        # )
        # params_widget = VBox([checkbox, add_params])
        raster_options = VBox([
            HBox([singular_band_dropdown_box]),
            HBox([palette_categories_dropdown_box]),
            HBox([palettes_radiobuttons_box]),
        ])
        stac_buttons = ToggleButtons(
            value=None,
            options=["Display "],
            icons=["map"],
            disabled=True,
            tooltips=["Display selected Item on the Map"],
        )
        buttons_box = Box([stac_buttons], layout=layouts["buttons"])
        stac_tab_labels = ['Catalog', 'Visualization']
        tab_widget_children = []
        stac_tab_widget = Tab()

        for label in stac_tab_labels:     
            tab_content = VBox()
            if label == 'Catalog':
                tab_content.children = [
                    catalogs_box,
                    collections_box,
                    collection_description_box,
                    collection_url_box,
                    collection_dates_box,
                    items_box
                ]
            elif label == 'Visualization':
                tab_content.children = [
                    raster_options
                ]
            tab_widget_children.append(tab_content)
        stac_tab_widget.children = tab_widget_children
        stac_tab_widget.titles = stac_tab_labels
        stac_widget.children = [
            # catalogs_box,
            # collections_box,
            # collection_description_box,
            # collection_url_box,
            # collection_dates_box,
            # items_box,
            # palettes_dropdown,
            # raster_options,
            stac_tab_widget,
            buttons_box,
            output
        ]
    

        def update_default_display_settings():
            assets = [i for i in self.stac_data["items"] if i["id"] == items_dropdown.value][0]["assets"]
            href = [i for i in self.stac_data["items"] if i["id"] == items_dropdown.value][0]["href"]
                      
            if len(assets.keys()) > 0:
                with output:
                    output.clear_output()
                    # print("ASSETS", assets)
                asset_keys = assets.keys()
                if "data" in asset_keys:
                    data_url = assets["data"].get_absolute_href()
                    print("DATA URL", data_url)
                    self.stac_data["data_url"] = data_url
                    metadata = Stac.get_metadata(titiler_stac_endpoint=titiler_stac_endpoint, url=data_url)
                    print("METADATA", metadata)
                    self.stac_data["metadata"] = metadata
                    if "message" in metadata:
                        print("MESSAGE: ", metadata["message"])
                    if "statistics" in metadata:
                        minv, maxv = metadata["statistics"]["1"]["min"], metadata["statistics"]["1"]["max"]
                        print("MIN/MAX", minv, maxv)
                    if "band_metadata" in metadata:
                        bands = [b for b in metadata["band_metadata"][0] if len(b) > 0]
                        default_bands = Stac.set_default_bands(bands)
                        # print("BANDS", default_bands)
                        if len(bands) == 1:
                            raster_options.children = [
                                HBox([singular_band_dropdown_box]),
                                HBox([palette_categories_dropdown_box]),
                                HBox([palettes_radiobuttons_box]),
                                # checkbox,
                                # params_widget,
                            ]
                            singular_band_dropdown.options = default_bands
                            singular_band_dropdown.value = default_bands[0]
                            # stac_tab_widget.selected_index = 1
                            stac_buttons.disabled = False
                        else:
                            raster_options.children = []                      
                            singular_band_dropdown.value = None
                
                    else:
                        print("\nDATA HAS 0 BANDS.")
            
                if "cog_default" in asset_keys:
                    data_url = assets["cog_default"].get_absolute_href()
                    self.stac_data["data_url"] = data_url
                    metadata = Stac.get_item_info(url=href)
                    self.stac_data["metadata"] = metadata
                    raw_bands = metadata["assets"]["cog_default"]["raster:bands"]
                    if "statistics" in raw_bands[0]:
                        minv, maxv = raw_bands[0]["statistics"]["minimum"], raw_bands[0]["statistics"]["maximum"]
                    
                    if len(raw_bands) == 1:
                        raster_options.children = [
                            HBox([singular_band_dropdown_box]),
                            HBox([palette_categories_dropdown_box]),
                            HBox([palettes_radiobuttons_box]),
                            # checkbox,
                            # params_widget,
                        ]
                        # singular_band_dropdown.options = ['1']
                        # singular_band_dropdown.value = ['1']
                        # stac_tab_widget.selected_index = 1
                        stac_buttons.disabled = False
                    
            else:
                print("This item cannot displayed. Only Cloud-Optimized GeoTIFFs are supported at this time.")
                

        def query_collection_items(selected_collection):
            # print("SELECTED TO QUERY", selected_collection)
            items_dropdown.options = []
            items_dropdown.value = None
            with output:
                output.clear_output()
                print("Retrieving items...")
                try:
                    # geometries = [self.draw_control.last_draw['geometry']]
                    # print(geometries)
                    if isinstance(collection_start_date.value, datetime):
                        start_date_query = collection_start_date.value.strftime("%Y-%m-%d")
                    else:
                        start_date_query = str(collection_start_date.value)

                    if isinstance(collection_end_date.value, datetime):
                        end_date_query = collection_end_date.value.strftime("%Y-%m-%d")
                    else:
                        end_date_query = str(collection_end_date.value)

                    _datetime = start_date_query 
                    if collection_end_date.value is not None:
                        _datetime = _datetime + "/" + end_date_query
                    url = selected_collection["href"]
                    _query_url = url if url.endswith("/items") else url + "/items"
                    
                    print("from ",_query_url, "...")

                    collection_items = Stac.stac_search(
                        url=_query_url,
                        max_items=20,
                        # intersects=geometries[0],
                        datetime=_datetime,
                        titiler_endpoint=self.titiler_endpoint,
                        get_info=True,
                    )
                    result_items = list(collection_items.values())
                    self.stac_data["items"] = result_items
                    options = list(collection_items.keys())
                    if len(options) > 0:
                        items_dropdown.options = options
                        output.clear_output()
                        print(f"{len(options)} items were found - please select 1 to determine if it can be displayed.")                        
                    else:
                        output.clear_output()
                        print("No items were found within this Collection. Please select another.")

                except Exception as err:
                    output.clear_output()
                    print("COLLECTION QUERY ERROR", err)


        # Event Watchers
        def catalogs_changed(change):
            if change["new"]:                
                selected_catalog = [cat for cat in stac_catalogs if cat["name"] == catalogs_dropdown.value][0]
                selected_collection_options = sorted([c for c in selected_catalog["collections"]], key=lambda c: c["id"])
                selected_collection = selected_collection_options[0]
                collections_dropdown.options = [c["id"] for c in selected_collection_options]
                collections_dropdown.value = selected_collection["id"]
                self.stac_data["catalog"] = selected_catalog
                self.stac_data["collection"] = selected_collection
                query_collection_items(selected_collection)
                
                # with output:
                #     output.clear_output()
                #     print(selected_collection["id"])

        catalogs_dropdown.observe(catalogs_changed, names="value")
        
        def collection_changed(change):
            if change["new"]:
                selected_collection = [c for c in selected_collection_options if c["id"] == collections_dropdown.value][0]
                collection_description.value = f'<div style="{styles["desc"]}">{selected_collection["description"]}</div>'
                collection_url.value = f'<a href={selected_collection["href"]} target="_blank">{selected_collection["href"]}</a>'
                stac_browser_url = selected_collection["href"].replace("https://", "https://stac-browser.maap-project.org/external/")
                collection_url_browser.value = f'<a href={stac_browser_url} target="_blank"><b>View in STAC Browser</b></a>'
                if selected_collection["start_date"] != "":
                    collection_start_date.value = datetime.strptime(selected_collection["start_date"], "%Y-%m-%d")
                else:
                    collection_start_date.value = None
                if selected_collection["end_date"] != "":
                    collection_end_date.value = datetime.strptime(selected_collection["end_date"], "%Y-%m-%d")
                else:
                    collection_end_date.value = None
                self.stac_data["collection"] = selected_collection
                query_collection_items(selected_collection)
                # raster_options.children = []

                # with output:
                #     output.clear_output()
                #     print(selected_collection)

        collections_dropdown.observe(collection_changed, names="value")
    
        def items_changed(change):
            if change["new"]:
                update_default_display_settings()
                # if not singular_band.options:
                #     with output:
                #         print("This item cannot displayed. Only Cloud-Optimized GeoTIFFs are supported at this time.")
                # vmin.value = ""
                # vmax.value = ""

        items_dropdown.observe(items_changed, names="value")

        def palette_category_changed(change):
            if change["new"]:
                new_palettes = list_palettes(lowercase=True, category=palette_categories_dropdown.value)
                palette_radiobuttons.options = new_palettes
                palette_radiobuttons.value = new_palettes[0]

        palette_categories_dropdown.observe(palette_category_changed, names="value")

        """ def reset_values():
            selected_collection = selected_collection_options[0]
            collections_dropdown.value = selected_collection["id"]
            collection_description.value = f'<div style="{styles["desc"]}">{selected_collection["description"]}</div>'
            collection_url.value = f'<a href={selected_collection["href"]} target="_blank">{selected_collection["href"]}</a>'
            collection_url_browser.value = f'<a href={selected_collection["href"]} target="_blank">View in Browser</a>'
            collection_start_date.value = datetime.strptime(selected_collection["start_date"], "%Y-%m-%d")
            collection_end_date.value = datetime.strptime(selected_collection["end_date"], "%Y-%m-%d")
            items_dropdown.options = []
            query_collection_items(selected_collection)
            # palette.value = None
            # raster_options.children = [] """


        def button_clicked(change):
            if change["new"] == "Display":
                with output:
                    output.clear_output()
                    if not items_dropdown.value == None:
                        print(f"Loading data for {items_dropdown.value}...")
                        # if (
                        #     checkbox.value
                        #     and add_params.value.strip().startswith("{")
                        #     and add_params.value.strip().endswith("}")
                        # ):
                        #     vis_params = eval(add_params.value)
                        # else:
                        vis_params = {}
                        
                        if (palette_radiobuttons.value and singular_band_dropdown.options) or (palette_radiobuttons.value and "expression" in vis_params):
                            vis_params["colormap_name"] = palette_radiobuttons.value

                        if vmin.value and vmax.value:
                            vis_params["rescale"] = f"{vmin.value},{vmax.value}"

                        if nodata.value:
                            vis_params["nodata"] = nodata.value

                        if singular_band_dropdown.options:
                            assets = singular_band_dropdown.value
                        else:
                            assets = ""

                        stac_url = Stac.get_tile_url(
                            url=self.stac_data["data_url"],
                            collection=self.stac_data["collection"]["id"],
                            item=items_dropdown.value,
                            assets=assets,
                            palette=vis_params["colormap_name"],
                            titiler_stac_endpoint=titiler_stac_endpoint
                        )
                        if "tiles" in stac_url:
                            self.stac_data["tiles_url"] = stac_url["tiles"][0]
                            try:
                                if "bounds" in self.stac_data["metadata"]:
                                    bounds = self.stac_data["metadata"]["bounds"]
                                else:
                                    bounds = self.stac_data["metadata"]["bbox"]

                                tile_url = self.stac_data["tiles_url"]
                                name = items_dropdown.value
                                attribution=name
                                self.add_tile_layer(url=tile_url, name=name, attribution=attribution)
                                self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
                                output.clear_output()
                                # print("STAC URL", stac_url["tiles"][0])
                            except Exception as err:
                                output.clear_output()
                                print("Display error: ", err)

            """ elif change["new"] == "Reset":
                reset_values() """

            """ elif change["new"] == "Close":
                stac_widget.layout.display = 'none' """

            stac_buttons.value = None

        stac_buttons.observe(button_clicked, "value")

        query_collection_items(selected_collection)

        stac_widget.layout.display = 'none'
        
        return stac_widget
