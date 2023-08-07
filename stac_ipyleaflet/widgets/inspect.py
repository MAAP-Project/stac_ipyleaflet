from ipyleaflet import DrawControl, MarkerCluster, Marker, DrawControl, GeoJSON
from urllib.parse import urlparse, parse_qs
from typing import List
from stac_ipyleaflet.constants import TITILER_ENDPOINT
from stac_ipyleaflet.core import StacIpyleaflet
from stac_ipyleaflet.utilities.helpers import make_get_request


class COGRequestedData:
    coordinates: List[float]
    values: List[float]
    band_names: List[str]


class LayerData:
    layer_name: str
    data: COGRequestedData


# @TODO: Break out shared logic between widgets into a utilities directory
class InspectControlWidget(StacIpyleaflet):
    def template(self):
        # @TODO-CLEANUP: Create only one DrawControl and pass in the attributes instead
        draw_control = DrawControl(
            edit=False,
            remove=False,
            circlemarker={},
            polygon={},
            polyline={},
            rectangle={},
        )

        draw_control.marker = {
            "repeatMode": False,
        }

        tabs = {}

        for i in range(2):
            tabs[f"child{i}"] = (
                self.interact_widget.children[0]
                .children[i]
                .children[0]
                .children[0]
                .children
            )

        point_tab_children = tabs["child0"]
        area_tab_children = tabs["child1"]

        point_data = point_tab_children[1]
        clear_button = point_tab_children[2]

        def get_visible_layers_data(coordinates) -> List[LayerData]:
            visible_layers_data = []
            cog_partial_request_path = (
                f"{TITILER_ENDPOINT}/cog/point/{coordinates[0]},{coordinates[1]}?url="
            )
            for layer in self.applied_layers:
                if "/cog" in layer.url:
                    parsed_url = urlparse(layer.url)
                    parsed_query = parse_qs(parsed_url.query)
                    url = parsed_query["url"][0]
                    data = make_get_request(f"{cog_partial_request_path}{url}")
                    if data:
                        visible_layers_data.append(
                            {"layer_name": layer.name, "data": data.json()}
                        )
                # @TODO: Add logic to grab point data for "/mosaics" layers here
                # @NOTE: Blocked until Impact Titiler is updated to access /mosaicsjson/point
            return visible_layers_data

        def display_layer_data(layers_data: LayerData):
            point_data.value = ""

            def create_layer_data_html(layer_name, coordinates, values, band_names):
                template = f"""
                    <p>
                        <b>
                            {layer_name}
                        </b>
                    </p>
                    <ul>
                        <li>
                            Coordinates: {coordinates}
                        </li>
                        <li>
                            Values: {values}
                        </li>
                        <li>
                            Bands: {band_names}
                        </li>
                    </ul>
                """
                return template

            for layer in layers_data:
                point_data.value += create_layer_data_html(
                    layer["layer_name"],
                    layer["data"]["coordinates"],
                    layer["data"]["values"],
                    layer["data"]["band_names"],
                )
            return

        def handle_interaction(event, action, geo_json, **kwargs):
            # @TODO-CLEANUP: Duplication between tabs, pull logic out into a common utilities file
            def handle_clear(event):
                draw_layer = self.find_layer("draw_layer")
                self.remove_layer(draw_layer)
                point_data.value = "<code>Waiting for points of interest...</code>"
                clear_button.disabled = True
                return

            event.coordinates = []
            if "Coordinates" in area_tab_children[1].value:
                area_tab_children[
                    1
                ].value = "<code>Waiting for area of interest...</code>"

            if action == "created":
                if geo_json["geometry"] and geo_json["geometry"]["type"] == "Point":
                    geojson_layer = GeoJSON(
                        name="draw_layer",
                        data=geo_json,
                    )
                    self.add_layer(geojson_layer)
                    event.coordinates = geo_json["geometry"]["coordinates"]

                    if len(self.applied_layers):
                        layers_data = get_visible_layers_data(event.coordinates)
                        if layers_data:
                            display_layer_data(layers_data)
                        else:
                            point_data.value = f"<p><b>Coordinates:</b></p><code>{event.coordinates}</code><br/>"
                    elif not len(self.applied_layers):
                        point_data.value = f"<p><b>Coordinates:</b></p><code>{event.coordinates}</code><br/>"

            event.clear()
            clear_button.disabled = False
            clear_button.on_click(handle_clear)
            return

        draw_control.on_draw(callback=handle_interaction)

        return draw_control
