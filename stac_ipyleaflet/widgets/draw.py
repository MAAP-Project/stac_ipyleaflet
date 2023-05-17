from ipyleaflet import DrawControl
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
                # aoi_copy_button = main.aoi_widget.children[2]
                
                if action == "deleted":
                    aoi_coords.value = "<code>Waiting for area of interest...</code>"
                    # aoi_copy_button.disabled = True
                if action == "created":
                    if geo_json["properties"]:
                        coords_raw = geo_json["geometry"]["coordinates"][0][0:-1] # remove last (duplicate) coords
                        coords_list = [coord for coord in coords_raw]
                        coords = ", ".join(map(str, coords_list))
                        # print(f"AOI Coordinates: {str(coords)}")
                        aoi_coords.value = f"<code>{coords}</code>"
                        # aoi_copy_button.disabled = False
        
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
