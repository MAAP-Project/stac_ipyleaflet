from ipyleaflet import DrawControl, GeoJSON
from ipywidgets import Box, Output
from stac_ipyleaflet.core import StacIpyleaflet


# @TODO: Break out shared logic between widgets into a utilities directory
class DrawControlWidget(StacIpyleaflet):
    def template(self) -> Box(style={"max_height: 200px"}):
        bbox_out = Output()

        # Set unwanted draw controls to False or empty objects
        # @TODO-CLEANUP: Create only one DrawControl and pass in the attributes instead
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

        aoi_coords = area_tab_children[1]
        aoi_clear_button = area_tab_children[2]

        # @TODO-CLEANUP: Duplication between tabs, pull logic out into a common utilities file
        def handle_clear(event):
            draw_layer = self.find_layer("draw_layer")
            self.remove_layer(draw_layer)
            aoi_coords.value = "<code>Waiting for area of interest...</code>"
            aoi_clear_button.disabled = True

        def handle_draw(event, action, geo_json, **kwargs):
            self.aoi_coordinates = []
            self.aoi_bbox = ()

            if "Coordinates" in point_tab_children[1].value:
                area_tab_children[
                    1
                ].value = "<code>Waiting for points of interest...</code>"

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
                    self.add_layer(geojson_layer)
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
                    self.aoi_coordinates = raw_coordinates
                    self.aoi_bbox = bbox
                    coords_list = [coord for coord in raw_coordinates]
                    coords = ",<br/>".join(map(str, coords_list))
                    aoi_coords.value = f"<p><b>Coordinates:</b></p><code>{coords}</code><br/><p><b>BBox:</b></p><code>{bbox}</code>"
                    event.clear()
                    aoi_clear_button.disabled = False
                    aoi_clear_button.on_click(handle_clear)

            return

        draw_control.on_draw(callback=handle_draw)
        draw_control.output = bbox_out

        return draw_control
