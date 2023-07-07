# STAC ipyleaflet

WORK IN PROGRESS. Right now this connects to the MAAP STAC - providing a module on top of ipyleaflet demonstrating how to load & control opacity for tile layers (from `biomass-layers.csv`), view pre-determined Basemaps, and derive coordinates from a user-defined bounding box.

Much of this project is inspired from [leafmap](https://leafmap.org/)

![Jupyter Lab ScreenShot](/public/images/jlab-screenshot.png)

## Additional requirements

* jupyter lab, node>=12.0.0

## Getting started locally
This project will run locally as a dev container which will need to be installed. If you are using VSCode, add the `Dev Containers` extension and then also install the `Remote Development` extensions. Conda is used to manage our base environment packages and then we will use pip to manage our libraries.

Once these have been installed, follow these steps below:
1. To start the dev container, click on the `Remote Development` extensions icon in the bottom left corner, and then from the options list choose `Reopen in Container`
2. Making sure you are at the root of `stac_ipyleaflet`, In the terminal in VSCode, run `conda activate base`. Your terminal should look something like this... with the red text referencing your branch name
![](/public/images/getting-started-conda-activate.png)
3. Run `conda init`
4. Run `pip install -r requirements.txt`
5. Run `jupyter lab` and this should reveal two links in the log, you would want to click and open any of those two!
![](/public/images/getting-started-links.png)
6. Once opening the link, click on the `demo.ipynb` file and run the code snippet to produce the map! If you can get the map to run, then you have successfully ran the code in your local env :raised_hands:

> Note: If you notice the the widgets (tabs) are not displaying the correct styling, stop the container and run `conda install -c conda-forge ipywidgets` then restart the container. This should fix this issue and the outcome if successful should look like... ![](/public/images/getting-started-correct-tabs.png)



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
