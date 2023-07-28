from ipyleaflet import DrawControl, GeoJSON, MarkerCluster, Marker, DrawControl
from ipywidgets import Box, Output, Checkbox, Layout

# from stac_ipyleaflet.core import StacIpyleaflet
# from ..constants import StacIpyleaflet


class InspectControlWidget:
    def __init__(self, applied_layers):
        super().__init__()
        # self.aoi_widget = aoi_widget
        # self.find_layer = find_layer
        # self.remove_layer = remove_layer
        # self.add_layer = add_layer
        self.applied_layers = applied_layers
        self.marker_cluster = MarkerCluster(name="Inspector Markers")
        self.inspector_add_marker = Checkbox(
            description="Add Marker at clicked location",
            value=True,
            indent=False,
            layout=Layout(padding="0px 6px 2px 6px", width="300px"),
        )
        # self.draw_control = DrawControl()

    def template(self):
        draw_control = DrawControl(
            edit=False,
            remove=False,
            circlemarker={},
            polygon={},
            polyline={},
            rectangle={},
        )
        # draw_control.rectangle = {}
        draw_control.marker = {
            "shapeOptions": {
                "fillColor": "transparent",
                "color": "#333",
                "fillOpacity": 1.0,
            },
            "repeatMode": False,
        }

        def handle_interaction(self, action, geo_json, **kwargs):
            print("handling interaction")
            # if not hasattr(self, "inspector_add_marker"):
            #     inspector_add_marker = Checkbox(
            #         description="Add Marker at clicked location",
            #         value=True,
            #         indent=False,
            #         layout=Layout(padding="0px 6px 2px 6px", width="300px"),
            #     )
            #     # setattr(m, "inspector_add_marker", inspector_add_marker)
            #     self.inspector_add_marker = inspector_add_marker
            # add_marker = self.inspector_add_marker
            # latlon = kwargs.get("coordinates")
            # lat = round(latlon[0], 4)
            # lon = round(latlon[1], 4)
            self.coordinates = []

            print(f"action here: ", action)

            if kwargs.get("type") == "click":
                self.default_style = {"cursor": "wait"}
                # with output:
                #     output.outputs = ()
                #     print("Getting pixel value ...")

                #     layer_dict = m.cog_layer_dict[dropdown.value]

                if self.applied_layers:
                    # if bands_chk.value:
                    #     assets = layer_dict["assets"]
                    # else:
                    # assets = None
                    assets = None

                    # @NOTE-SANDRA: Implement call to get pixel value
                    # result = stac_pixel_value(
                    #     lon,
                    #     lat,
                    #     layer_dict["url"],
                    #     layer_dict["collection"],
                    #     layer_dict["item"],
                    #     assets,
                    #     layer_dict["titiler_endpoint"],
                    #     verbose=False,
                    # )
                    result = "test"
                    if result is not None:
                        # with output:
                        #     output.outputs = ()
                        #     print(f"lat/lon: {lat:.4f}, {lon:.4f}\n")
                        #     for key in result:
                        #         print(f"{key}: {result[key]}")

                        #     result["latitude"] = lat
                        #     result["longitude"] = lon
                        #     result["label"] = label.value
                        #     m.pixel_values.append(result)
                        if add_marker.value:
                            markers = list(self.marker_cluster.markers)
                            markers.append(Marker(location=latlon))
                            self.marker_cluster.markers = markers

        draw_control.on_draw(callback=handle_interaction)
        return draw_control
