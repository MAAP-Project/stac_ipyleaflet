from ipyleaflet import DrawControl, MarkerCluster, Marker, DrawControl, GeoJSON
from urllib.parse import urlparse, parse_qs
from typing import List


class COGRequestedData:
    coordinates: List[float]
    values: List[float]
    band_names: List[str]


class LayerData:
    layer_name: str
    data: COGRequestedData


# @NOTE: This should be an extension of the IPYLEAFLET Class. Currently it is just being passed
# in instead due to import errors
class InspectControlWidget:
    def template(
        self, applied_layers, interact_widget, make_get_request, titiler_endpoint
    ):
        main = self
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

        interact_tab = (
            interact_widget.children[0].children[0].children[0].children[0].children
        )
        point_data = interact_tab[1]
        clear_button = interact_tab[2]

        def get_visible_layers_data(coordinates) -> List[LayerData]:
            visible_layers_data = []
            cog_partial_request_path = (
                f"{titiler_endpoint}/cog/point/{coordinates[0]},{coordinates[1]}?url="
            )
            for layer in applied_layers:
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

        def display_data(layers_data: LayerData):
            point_data.value = ""

            def create_html_template(layer_name, coordinates, values, band_names):
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
                point_data.value += create_html_template(
                    layer["layer_name"],
                    layer["data"]["coordinates"],
                    layer["data"]["values"],
                    layer["data"]["band_names"],
                )
            return

        def handle_interaction(self, action, geo_json, **kwargs):
            def handle_clear(event):
                draw_layer = main.find_layer("draw_layer")
                main.remove_layer(draw_layer)
                point_data.value = "<code>Waiting for points of interest...</code>"
                clear_button.disabled = True
                return

            self.coordinates = []

            if action == "created":
                if geo_json["geometry"] and geo_json["geometry"]["type"] == "Point":
                    geojson_layer = GeoJSON(
                        name="draw_layer",
                        data=geo_json,
                    )
                    main.add_layer(geojson_layer)
                    self.coordinates = geo_json["geometry"]["coordinates"]

                    if len(applied_layers):
                        layers_data = get_visible_layers_data(self.coordinates)
                        if layers_data:
                            display_data(layers_data)
                        else:
                            point_data.value = f"<p><b>Coordinates:</b></p><code>{self.coordinates}</code><br/>"
                    elif not len(applied_layers):
                        point_data.value = f"<p><b>Coordinates:</b></p><code>{self.coordinates}</code><br/>"
            self.clear()
            clear_button.disabled = False
            clear_button.on_click(handle_clear)
            return

        draw_control.on_draw(callback=handle_interaction)

        return draw_control
