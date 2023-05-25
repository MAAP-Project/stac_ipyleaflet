# STAC ipyleaflet

WORK IN PROGRESS. Right now this connects to the MAAP STAC - providing a module on top of ipyleaflet demonstrating how to load & control opacity for tile layers (from `biomass-layers.csv`), view pre-determined Basemaps, and derive coordinates from a user-defined bounding box.

Much of this project is inspired from [leafmap](https://leafmap.org/)

![Jupyter Lab ScreenShot](jlab-screenshot.png)

## Additional requirements

* jupyter lab, node>=12.0.0

## Setup

For demo purposes, `write_biomass_layers.py` creates a CSV file with current map layers.
```sh
conda create -n stac_ipyleaflet python=3.9
conda activate stac_ipyleaflet
pip install -r requirements.txt
python -m ipykernel install --user --name=stac_ipyleaflet
export AWS_PROFILE=maap
jupyter lab
```

Note this library currently includes `rio.open` so must be run with an AWS identity that has access to the bucket the biomass products are in.

**Styling Notes**
- By default, ipywidget icons can be set to any from the font-awesome library v4: https://fontawesome.com/v4/icons/
- By default, ipywidget buttons can be styled to any html colors: https://htmlcolorcodes.com/color-names/
