# STAC ipyleaflet Docs

### This documentation section provides *sample* Jupyter notebooks to demonstrate how to extend the current version of the `stac_ipyleaflet` library beyond the included widgets. 

_Browse through the sample notebooks within the `/sample_notebooks` directory to learn how to load and visualize geospatial datasets that are outside of a STAC Catalog, but within your cloud development environment or publicly accessible over the web._

Since `stac_ipyleaflet` is built on top of ipyleaflet, additional layer types can be added by following the [ipyleaflet documentation](https://ipyleaflet.readthedocs.io/en/latest/layers/index.html).



## Sample Notebooks

- [visualize-**geodataframe**.ipynb](./sample_notebooks/visualize-geodataframe.ipynb): Load a geojson file located within your cloud development environment as a Pandas Geodataframe, create a **GeoData Layer** and add it to the interactive map.

- [visualize-**geojson**.ipynb](./sample_notebooks/visualize-geojson.ipynb): Load a geojson file located within your cloud development environment, create a **GeoJSON Layer** and add it to the interactive map.

- [visualize-**mosaic**.ipynb](./sample_notebooks/visualize-mosaic.ipynb): Create a mosaic from an array of COG rasters that are located within your cloud development environment, load it as a **Tile Layer** and add it to the interactive map.

- [visualize-**raster**.ipynb](./sample_notebooks/visualize-raster.ipynb): Load a raster within your cloud development environment, create a **Tile Layer** and add it to the interactive map.

- [visualize-**wms**.ipynb](./sample_notebooks/visualize-geojson.ipynb): Create a **WMS Layer** from a publicly accessible URL and add to the interactive map.




