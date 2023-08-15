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
            for layer in self.applied_layers:
                if "/cog" in layer.url:
                    parsed_url = urlparse(layer.url)
                    parsed_query = parse_qs(parsed_url.query)
                    url = parsed_query["url"][0]
                    cog_partial_request_path = f"{TITILER_ENDPOINT}/cog/point/{coordinates[0]},{coordinates[1]}?url="
                    response = make_get_request(f"{cog_partial_request_path}{url}")
                    if response.status_code == 200:
                        data = response.json()
                        visible_layers_data.append(
                            {"layer_name": layer.name, "data": data}
                        )
                elif "/mosaics" in layer.url:
                    parsed_url = urlparse(layer.url)
                    mosaic_id = parsed_url.path.split("/")[2]
                    mosaic_request_url = f"{TITILER_ENDPOINT}/mosaics/{mosaic_id}/point/{coordinates[0]},{coordinates[1]}"
                    response = make_get_request(mosaic_request_url)
                    data = response.json()
                    if response.status_code == 200:
                        data_to_display = {
                            "coordinates": data["coordinates"],
                            "values": data["values"][0][1],
                            "band_names": data["values"][0][-1],
                        }
                        visible_layers_data.append(
                            {"layer_name": layer.name, "data": data_to_display}
                        )
                    if response.status_code == 404:
                        visible_layers_data.append({"layer_name": layer.name, **data})
            return visible_layers_data

        def display_layer_data(coordinates: List[int], layers_data: LayerData):
            point_data.value = f"""
                    <p>
                        Coordinates: {coordinates}
                    </p>
                """

            def create_layer_data_html(layer_name, values, band_names):
                return f"""
                    <p>
                        <b>
                            {layer_name}
                        </b>
                    </p>
                    <ul>
                        <li>
                            Values: {values}
                        </li>
                        <li>
                            Bands: {band_names}
                        </li>
                    </ul>
                """

            def create_no_data_html(layer_name, msg):
                return f"""
                    <p>
                        <b>
                            {layer_name}
                        </b>
                    </p>
                    <p>
                        {msg}
                    </p>
                """

            for layer in layers_data:
                if "data" in layer:
                    point_data.value += create_layer_data_html(
                        layer["layer_name"],
                        layer["data"]["values"],
                        layer["data"]["band_names"],
                    )
                elif "data" not in layer and "detail" in layer:
                    point_data.value += create_no_data_html(
                        layer["layer_name"], layer["detail"]
                    )
                else:
                    point_data.value += create_no_data_html(
                        layer["layer_name"], "No data to report"
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
                            display_layer_data(event.coordinates, layers_data)
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
