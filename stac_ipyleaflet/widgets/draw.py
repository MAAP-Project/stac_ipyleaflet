from ipyleaflet import DrawControl, Polygon, Rectangle
from ipywidgets import Box, Output

class DrawControlWidget():
    def template(self, **kwargs) -> Box( style={"max_height: 200px"} ):   
        main = self
        bbox_out = Output()

        # Set unwanted draw controls to False or empty objects
        draw_control = DrawControl(
            edit=False,
            # remove=False,
            circlemarker = {},
            polygon = {},
            polyline = {},            
        )        
        
        
        def handle_draw(self, action, geo_json):
                aoi_coords = main.aoi_widget.children[1]
                main.aoi_coordinates = []
                main.aoi_bbox = ()
                
                if action == "deleted":
                    aoi_coords.value = "<code>Waiting for area of interest...</code>"
                    main.aoi_coordinates = []
                    main.aoi_bbox = ()
                if action == "created":
                    if geo_json["geometry"]:
                        raw_coordinates = geo_json["geometry"]["coordinates"][0]
                        def bounding_box(points):
                            x_coordinates, y_coordinates = zip(*points)
                            return ((min(y_coordinates), min(x_coordinates)), (max(y_coordinates), max(x_coordinates)))
                        bbox = bounding_box(raw_coordinates)
                        main.aoi_coordinates = raw_coordinates
                        main.aoi_bbox = bbox
                        coords_list = [coord for coord in raw_coordinates]
                        coords = (",<br/>".join(map(str, coords_list)))
                        aoi_coords.value = f"<p><b>Coordinates:</b></p><code>{coords}</code><br/><p><b>BBox:</b></p><code>{bbox}</code>"
        
        draw_control.on_draw(callback=handle_draw)

        # Add rectangle draw control for bounding box
        draw_control.rectangle = {
            "shapeOptions": {
                "fillColor": "transparent",
                "color": "#333",
                "fillOpacity": 1.0
            }
        }
        draw_control.output = bbox_out
        
        return draw_control
