from ipyleaflet import DrawControl, MarkerCluster, Marker, DrawControl
from urllib.parse import urlparse, parse_qs
from typing import List


class COGRequestedData:
    coordinates: List[float]
    values: List[float]
    band_names: List[str]


class LayerData:
    layer_name: str
    data: COGRequestedData


class InspectControlWidget:
    def template(
        self, applied_layers, interact_widget, make_get_request, titiler_endpoint
    ):
        main = self
        marker_cluster = list(MarkerCluster().markers)
        draw_control = DrawControl(
            edit=False,
            remove=False,
            circlemarker={},
            polygon={},
            polyline={},
            rectangle={},
        )

        draw_control.marker = {
            "shapeOptions": {
                "fillColor": "transparent",
                "color": "#333",
                "fillOpacity": 1.0,
            },
            "repeatMode": False,
        }

        interact_tab = (
            interact_widget.children[0].children[0].children[0].children[0].children
        )
        point_coords = interact_tab[1]
        clear_button = interact_tab[2]

        def get_visible_layers_data(coordinates) -> List[LayerData]:
            visible_layers_data = []
            cog_partial_request_path = (
                f"{titiler_endpoint}/cog/point/{coordinates[0]},{coordinates[1]}?url="
            )
            # mosaics_partial_request_path = f"{titiler_endpoint}/mosaicjson/point/{coordinates[0]},{coordinates[1]}"
            # mosaics_partial_request_path = f"{titiler_endpoint}/mosaicjson[74c9966e-e865-4c6b-bfe8-d12130f9d6ad]/point/{coordinates[0]},{coordinates[1]}"
            # mosaics_partial_request_path = f"{cog_partial_request_path}s3://nasa-maap-data-store/file-staging/nasa-map/icesat2-boreal/boreal_agb_202302031675450331_0225.tif"
            mosaics_partial_request_path = f"{cog_partial_request_path}s3://nasa-maap-data-store/file-staging/nasa-map/NASA_JPL_global_agb_mean_2020/global_008_06dc_agb_mean_prediction_2020_mosaic_veg_gfccorr_scale1_SAmerica_cog.tif"
            for layer in applied_layers:
                if "/cog" in layer.url:
                    parsed_url = urlparse(layer.url)
                    parsed_query = parse_qs(parsed_url.query)
                    url = parsed_query["url"][0]
                    print(f"cog_url: {cog_partial_request_path}{url}")
                    data = make_get_request(f"{cog_partial_request_path}{url}")
                    if data:
                        visible_layers_data.append(
                            {"layer_name": layer.name, "data": data.json()}
                        )
                # @NOTE-SANDRA: This is currently not working
                if "/mosaics" in layer.url:
                    data = make_get_request(mosaics_partial_request_path)
                    print(f"mosaic_url: {mosaics_partial_request_path}")
                    print(f"mosaic_data: {data}")
                    if data:
                        visible_layers_data.append(
                            {"layer_name": layer.name, "data": data.json()}
                        )
            print(f"visible_layers_data: {visible_layers_data}")
            return visible_layers_data

        def display_data(layers_data: LayerData):
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
                point_coords.value += create_html_template(
                    layer["layer_name"],
                    layer["data"]["coordinates"],
                    layer["data"]["values"],
                    layer["data"]["band_names"],
                )
            return

        def handle_interaction(self, action, geo_json, **kwargs):
            def handle_clear(event):
                self.clear()  # NOTE: This will likely clear the aoi drawing as well...
                point_coords.value = "<code>Waiting for points of interest...</code>"
                clear_button.disabled = True
                return

            self.coordinates = []

            if action == "created":
                if geo_json["geometry"] and geo_json["geometry"]["type"] == "Point":
                    self.coordinates = geo_json["geometry"]["coordinates"]
                    marker_cluster.append(
                        Marker(location=(self.coordinates[0], self.coordinates[1]))
                    )
                    print(f"applied_layers: {applied_layers}")
                    point_coords.value = f"<p><b>Coordinates:</b></p><code>{self.coordinates}</code><br/>"
                    if len(applied_layers):
                        layers_data = get_visible_layers_data(self.coordinates)
                        if layers_data:
                            display_data(layers_data)
            clear_button.disabled = False
            clear_button.on_click(handle_clear)
            return

        draw_control.on_draw(callback=handle_interaction)

        return draw_control
