from ipyleaflet import basemaps, basemap_to_tiles, TileLayer
from ipywidgets import Box

class BasemapsWidget():
    def template(self, **kwargs) -> Box():
        base_layers = []
        def make_base_layer (url=None, visible=False, name="", layer=""):
            if url:
                layer = TileLayer(
                    url=url, 
                    name=name, 
                    base=True, 
                    visible=False, 
                    **kwargs
                )
                return layer
            else:
                layer = basemap_to_tiles(layer)
                layer.base = True
                layer.visible = visible
                layer.name = name
                return layer            
        
        tile_layers = [
            {
                "url": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
                "name": "Google Terrain"
            },
            {
                "url": "http://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                "name": "Esri Light Gray"
            },
        ]
        
        for tl in tile_layers:
            tile_layer = make_base_layer(url=tl["url"], name=tl["name"])
            base_layers.append(tile_layer)
        
        basemap_layers = [
            {
                "layer": basemaps.Esri.WorldImagery,
                "name": "Esri World Imagery"
            },
            {
                "layer": basemaps.Esri.NatGeoWorldMap,
                "name": "Esri National Geographic"
            },
            {
                "layer": basemaps.OpenStreetMap.Mapnik,
                "name": "Open Street Map"
            },
            {
                "layer": basemaps.OpenTopoMap,
                "name": "Open Topo Map"
            },
            {
                "layer": basemaps.Stamen.Toner,
                "name": "Black & White"
            },
            {
                "layer": basemaps.Strava.Water,
                "name": "Water"
            },
        ]
        
        for bm in basemap_layers:
            if bm["name"] == "Open Street Map":
                bm_layer = make_base_layer(layer=bm["layer"], name=bm["name"], visible=True)
            else:
                bm_layer = make_base_layer(layer=bm["layer"], name=bm["name"])
            base_layers.append(bm_layer)
        
        return base_layers
