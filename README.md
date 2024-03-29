# STAC ipyleaflet

[![DOI](https://zenodo.org/badge/591005076.svg)](https://zenodo.org/doi/10.5281/zenodo.10015863)

### What
stac_ipyleaflet is a customized version of [ipyleaflet](https://ipyleaflet.readthedocs.io/en/latest/) built to be an in-jupyter-notebook interactive mapping library that prioritizes access to STAC catalog data. The library provides ([ipywidgets](https://ipywidgets.readthedocs.io/en/stable/)-based) components that are meant to help users working in Jupyter Notebook environments to quickly visualize and interact with geospatial data at different stages throughout their research process.

### Why
The intended users of this library are members of the scientific community who are doing research in areas like climate and active remote sensing. While they can write code to visualize and analyze data, they find it time consuming and may end up exporting results to visualize/explore data in & out of a jupyter notebook. This library allows them to visualize remotely sensed data as quickly as possible at scale as fast as possible right in the notebook. It does not replace full featured GIS tools but offers enough visualization capabilities to support their scientific analysis cycles.

![stac_ipyleaflet as part of the explore/visualization solution](/public/images/about-map-visualization-solution.png)
> stac_ipyleaflet as part of the explore/visualization solution

WORK IN PROGRESS. Right now this connects to the MAAP STAC - providing a module on top of ipyleaflet demonstrating how to load & control opacity for tile layers (from `biomass-layers.csv`), view pre-determined Basemaps, and derive coordinates from a user-defined bounding box.

Much of this project is inspired from [leafmap](https://leafmap.org/)

![Jupyter Lab ScreenShot](/public/images/jlab-screenshot.png)

## Features
* Layers widget with Biomass and Basemap layers with opacity control
* STAC integration to display COGs on map
* Ability to draw AOI and copy coordinates

## Contributing
To contribute to this codebase, clone this repository down and create a new branch. All PRs should be against the `main` branch. Branch names should be prefixed with either *feature, fix, docs, refactor, cleanup* and be in kebab-case format.

For example when adding documentation, the branch name should look something like `docs/{special-branch-name}`. Or when refactoring for code optimization, the branch name should look something like `refactor/{special-branch-name}`

### Testing
### Unit Testing with Pytest
@TODO: To Be Developed further...Think about what is the point of testing? We should just test for core pieces of functionality and not stick so closely to a threshold?

**How to run unit tests**

From the root of this project and in your dev container environment. Run `pytest` in the terminal. If you want to enable logging, run `pytest -s`. 

### Manual Testing
To test new features or changes in the `Algorithm Development Environment` (ADE). Navigate to your jupyter notebook's terminal and run the following...
1. `pip uninstall stac_ipyleaflet`
2. `pip install git+https://github.com/MAAP-Project/stac_ipyleaflet.git#egg-info=stac_ipyleaflet`
This should install `stac_ipyleaflet` with the latest commits from the `main` branch
> Note: pip installing with the `--upgrade` flag will not work unless a change in version in the `setup.cfg` file was detected

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
5. Create a `.env` file at the root of this codebase. The file should contain and look like...
```
TITILER_STAC_ENDPOINT=https://titiler-stac.maap-project.org
TITILER_ENDPOINT=https://titiler.maap-project.org
STAC_CATALOG_NAME=MAAP STAC
STAC_CATALOG_URL=https://stac.maap-project.org
STAC_BROWSER_URL=https://stac-browser.maap-project.org/external/
```
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
