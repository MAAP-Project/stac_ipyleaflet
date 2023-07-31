from ipyleaflet import DrawControl, GeoJSON
from ipywidgets import Box, Output


# TODO: Fix linting errors caused by inferred inheritance and just pass in params instead
class DrawControlWidget:
    def template(self, **kwargs) -> Box(style={"max_height: 200px"}):
        main = self
        bbox_out = Output()

        # Set unwanted draw controls to False or empty objects
        draw_control = DrawControl(
            edit=False,
            remove=False,
            circlemarker={},
            polygon={},
            polyline={},
            marker={},
        )

        # Add rectangle draw control for bounding box
        draw_control.rectangle = {
            "shapeOptions": {
                "fillColor": "transparent",
                "color": "#333",
                "fillOpacity": 1.0,
            },
            "repeatMode": False,
        }

        area_tab = (
            main.interact_widget.children[0]
            .children[1]
            .children[0]
            .children[0]
            .children
        )
        aoi_coords = area_tab[1]
        aoi_clear_button = area_tab[2]

        def handle_clear(self):
            draw_layer = main.find_layer("draw_layer")
            main.remove_layer(draw_layer)
            aoi_coords.value = "<code>Waiting for area of interest...</code>"
            aoi_clear_button.disabled = True

        def handle_draw(self, action, geo_json, **kwargs):
            main.aoi_coordinates = []
            main.aoi_bbox = ()

            if action == "created":
                if geo_json["geometry"]:
                    geojson_layer = GeoJSON(
                        name="draw_layer",
                        data=geo_json,
                        style={
                            "fillColor": "transparent",
                            "color": "#333",
                            "weight": 3,
                        },
                    )
                    main.add_layer(geojson_layer)
                    raw_coordinates = geo_json["geometry"]["coordinates"][0]

                    def bounding_box(points):
                        x_coordinates, y_coordinates = zip(*points)
                        return (
                            min(x_coordinates),
                            min(y_coordinates),
                            max(x_coordinates),
                            max(y_coordinates),
                        )

                    bbox = bounding_box(raw_coordinates)
                    main.aoi_coordinates = raw_coordinates
                    main.aoi_bbox = bbox
                    coords_list = [coord for coord in raw_coordinates]
                    coords = ",<br/>".join(map(str, coords_list))
                    aoi_coords.value = f"<p><b>Coordinates:</b></p><code>{coords}</code><br/><p><b>BBox:</b></p><code>{bbox}</code>"
                    self.clear()
                    aoi_clear_button.disabled = False
                    aoi_clear_button.on_click(handle_clear)

            return

        draw_control.on_draw(callback=handle_draw)
        draw_control.output = bbox_out

        return draw_control
