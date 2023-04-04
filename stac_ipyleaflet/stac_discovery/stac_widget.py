from ipywidgets import VBox, Output, Layout, Text, ToggleButtons, Dropdown, DatePicker, HBox, Textarea, Checkbox
import pandas as pd
import ipyevents
from datetime import datetime
from pathlib import Path
from typing import Any
from .stac import Stac

class StacDiscoveryWidget():
    def template(self) -> VBox():
        standard_width = "400px"
        padding = "0px 0px 0px 5px"
        style = {"description_width": "initial"}
        output = Output(
            layout=Layout(width=standard_width, padding=padding, overflow="auto")
        )
        stac_data = []

        # Templates for the STAC Discovery Widget
        stac_widget = VBox()
        padding = "0px 0px 0px 5px"
        style = {"description_width": "initial"}

        nasa_cmr_path = Path("stac_ipyleaflet/stac_discovery/catalogs/nasa_maap_stac.tsv")
        stac_info = {
            "MAAP STAC": {
                "filename": nasa_cmr_path,
                "name": "id",
                "url": "href",
                "description": "title",
            }
        }

        connections = list(stac_info.keys())

        # Template
        catalogs = Dropdown(
            options=connections,
            value="MAAP STAC",
            description="Catalog:",
            style=style,
            layout=Layout(width="450px", padding=padding),
        )

        df = pd.read_csv(stac_info[catalogs.value]["filename"], sep="\t")
        datasets = df[stac_info[catalogs.value]["name"]].tolist()
        default = df.iloc[0] # values mapped to .tsv

        collection = Dropdown(
            options=datasets,
            value=default["id"],
            description="Collection:",
            style=style,
            layout=Layout(width="450px", padding=padding),
        )
        collection_description = Text(
            value=default["description"],
            description="Description:",
            style=style,
            layout=Layout(width="450px", padding=padding),
        )
        collection_url = Text(
            value=default["href"],
            description="URL:",
            tooltip="STAC Catalog URL",
            style=style,
            layout=Layout(width="450px", padding=padding),
        )
        start_date = DatePicker(
            value=datetime.strptime(default["start_date"], "%Y-%m-%d"),
            description="Start:",
            disabled=False if collection.value else True,
            style=style,
            layout=Layout(width="215px", padding=padding),
        )
        end_date = DatePicker(
            value=datetime.strptime(default["end_date"], "%Y-%m-%d"),
            description="End:",
            disabled=False if collection.value else True,
            style=style,
            layout=Layout(width="215px", padding=padding),
        )
        items = Dropdown(
            options=[],
            description="Item:",
            style=style,
            layout=Layout(width="450px", padding=padding),
        )
        layer_name = Text(
            value="STAC Layer",
            description="Layer name:",
            tooltip="Enter a layer name for the selected file",
            style=style,
            layout=Layout(width="454px", padding=padding),
        )

        band_width = "125px"
        singular_band = Dropdown(
            description="Band:",
            tooltip="Present Band",
            style=style,
            layout=Layout(width=band_width, padding=padding),
        )

        vmin = Text(
            value=None,
            description="vmin:",
            tooltip="Minimum value of the raster to visualize",
            style=style,
            layout=Layout(width="148px", padding=padding),
        )
        vmax = Text(
            value=None,
            description="vmax:",
            tooltip="Maximum value of the raster to visualize",
            style=style,
            layout=Layout(width="148px", padding=padding),
        )
        nodata = Text(
            value=None,
            description="Nodata:",
            tooltip="Nodata the raster to visualize",
            style=style,
            layout=Layout(width="150px", padding=padding),
        )

        def list_palettes(add_extra=False, lowercase=False):
            """List all available colormaps. See a complete lost of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.
            Returns:
                list: The list of colormap names.
            """
            import matplotlib.pyplot as plt

            result = plt.colormaps()
            if add_extra:
                result += ["dem", "ndvi", "ndwi"]
            if lowercase:
                result = [i.lower() for i in result]
            result.sort()
            return result

        palette_options = list_palettes(lowercase=True)
        palette = Dropdown(
            options=palette_options,
            value=None,
            description="palette:",
            layout=Layout(width="300px", padding=padding),
            style=style,
        )
        # TODO: Add STAC layers to LayerGroup instead of base
        # TODO: Add LayerGroup control to utilize STAC LayerGroup
        # TODO: Add back in Checkbox for layer name and additional visual parameters
        # checkbox = Checkbox(
        #     value=False,
        #     description="Additional params",
        #     indent=False,
        #     layout=Layout(width="154px", padding=padding),
        #     style=style,
        # )
        # add_params_text = "Additional parameters in the format of a dictionary, for example, \n {'palette': ['#006633', '#E5FFCC', '#662A00', '#D8D8D8', '#F5F5F5'], 'expression': '(SR_B5-SR_B4)/(SR_B5+SR_B4)'}"
        # add_params = Textarea(
        #     value="",
        #     placeholder=add_params_text,
        #     layout=Layout(width="450px", padding=padding),
        #     style=style,
        # )
        # params_widget = VBox()
        raster_options = VBox()
        buttons = ToggleButtons(
            value=None,
            options=["Search", "Display", "Reset", "Close"],
            tooltips=["Search Collection", "Display Image", "Reset Values", "Close"],
            button_style="primary",
            style={"button_width": "50px"},
            padding="5px 0px 0px 5px"
        )
        buttons.style.button_width ="50px"
        stac_widget.children = [
            catalogs,
            collection,
            collection_description,
            collection_url,
            HBox([start_date, end_date]),
            items,
            raster_options,
            buttons,
            output
        ]

        # Event Watchers
        def catalogs_changed(change):
            if change["new"]:
                df = pd.read_csv(stac_info[catalogs.value]["filename"], sep="\t")
                datasets = df[stac_info[catalogs.value]["name"]].tolist()
                collection.options = datasets
                collection.value = datasets[0]

        catalogs.observe(catalogs_changed, names="value")

        def collection_changed(change):
            if change["new"]:
                output.clear_output()
                df = pd.read_csv(stac_info[catalogs.value]["filename"], sep="\t")
                df = df[df[stac_info[catalogs.value]["name"]] == collection.value]
                collection_description.value = df[stac_info[catalogs.value]["description"]].tolist()[0]
                collection_url.value = df[stac_info[catalogs.value]["url"]].tolist()[0]
                
                current_collection_index = df.index[df["id"] == collection.value].tolist()
                start_date.value = datetime.strptime(df["start_date"][current_collection_index].values[0], "%Y-%m-%d")
                end_date.value = datetime.strptime(df["end_date"][current_collection_index].values[0], "%Y-%m-%d")
                items.options = []
                raster_options.children = []

        collection.observe(collection_changed, names="value")

        def update_bands():
            assets = stac_data[0][items.value]["assets"]
            bands = [x for x in assets if assets[x].media_type and ("cloud-optimized" in assets[x].media_type)]

            if len(bands) == 1:
                raster_options.children = [
                    HBox([singular_band]),
                    HBox([palette]), # checkbox
                    # params_widget,
                ]
                singular_band.options = bands
            else:
                raster_options.children = []

            default_bands = Stac.set_default_bands(bands)
            try:
                singular_band.value = default_bands[0]
            except Exception as e:
                singular_band.value = None

    
        def items_changed(change):
            if change["new"]:
                output.clear_output()
                layer_name.value = items.value
                update_bands()
                if not singular_band.options:
                    with output:
                        print("This item cannot be added as a layer. Only cloud-optimized geotiffs are supported at this time.")
                vmin.value = ""
                vmax.value = ""

        items.observe(items_changed, names="value")

        def reset_values():
            collection.value = default["id"]
            collection_description.value = default["description"]
            collection_url.value = default["href"]
            start_date.value = datetime.strptime(default["start_date"], "%Y-%m-%d")
            end_date.value = datetime.strptime(default["end_date"], "%Y-%m-%d")
            palette.value = None
            items.options = []
            raster_options.children = []


        def button_clicked(change):
            if change["new"] == "Search":
                with output:
                    output.clear_output()

                    print("Retrieving items...")
                    try:
                        geometries = [self.draw_control.last_draw['geometry']]

                        if isinstance(start_date.value, datetime):
                            start_date_query = str(start_date.value.date())
                        else:
                            start_date_query = str(start_date.value)
                        if isinstance(end_date.value, datetime):
                            end_date_query = str(end_date.value.date())
                        else:
                            end_date_query = str(end_date.value)

                        _datetime = start_date_query + "/" + end_date_query

                        search = Stac.stac_search(
                            url=collection_url.value if collection_url.value.endswith("/items") else collection_url.value + "/items",
                            max_items=20,
                            intersects=geometries[0],
                            datetime=_datetime,
                            titiler_endpoint=self.titiler_endpoint,
                            get_info=True,
                        )
                        stac_data.clear()
                        stac_data.append(search)

                        output.clear_output()

                        items.options = list(search.keys())
                        items.value = list(search.keys())[0]

                    except Exception as e:
                        print(e)

            elif change["new"] == "Display":
                with output:
                    output.clear_output()
                    if items.value:
                        print("Loading data...")
                        # if (
                        #     checkbox.value
                        #     and add_params.value.strip().startswith("{")
                        #     and add_params.value.strip().endswith("}")
                        # ):
                        #     vis_params = eval(add_params.value)
                        # else:
                        vis_params = {}

                        if (palette.value and singular_band.options) or (palette.value and "expression" in vis_params):
                            vis_params["colormap_name"] = palette.value

                        if vmin.value and vmax.value:
                            vis_params["rescale"] = f"{vmin.value},{vmax.value}"

                        if nodata.value:
                            vis_params["nodata"] = nodata.value

                        if singular_band.options:
                            assets = singular_band.value
                        else:
                            assets = ""
                        try:
                            Stac.add_stac_layer(
                                self,
                                url=stac_data[0][items.value]["href"],
                                collection=collection.value,
                                item=items.value,
                                assets=assets,
                                name=layer_name.value,
                                titiler_stac_endpoint=self.titiler_stac_endpoint,
                                **vis_params,
                            )
                            self.stac_data = stac_data[0][items.value]
                            output.clear_output()
                        except Exception as e:
                            print(e)


            elif change["new"] == "Reset":
                reset_values()

            elif change["new"] == "Close":
                stac_widget.layout.display = 'none'

            buttons.value = None

        buttons.observe(button_clicked, "value")

        stac_widget.layout.display = 'none'
        
        return stac_widget
