from ipyleaflet import DrawControl
from ipywidgets import Box, Output

class DrawControlWidget():
    def template(self, **kwargs) -> Box():
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
            with bbox_out:                                
                if action == "deleted":
                    bbox_out.clear_output()
                if action == "created":
                    bbox_out.clear_output()
                    if geo_json["properties"]:
                        coords = geo_json["geometry"]["coordinates"][0][0:-1] # remove last (duplicate) coords
                        print("AOI Coordinates:", coords)                      
        
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
