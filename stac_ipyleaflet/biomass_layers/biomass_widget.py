import csv

import numpy
import xarray as xr
from ipywidgets import (
    Output,
    VBox,
)
from ipyleaflet import (
    Popup,
    display
)
from rio_tiler.io import Reader
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
import matplotlib.pyplot as plt
from ..base_widget import TileLayer
from .histograms import Histograms

class BiomassLayersWidget():
    def template():
        pass

    def add_biomass_layers(self):
        biomass_file = "biomass-layers.csv"
        with open(biomass_file, newline="") as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None)  # skip the headers
            for row in csv_reader:
                name, tile_url = row[0], row[1]
                tile_layer = TileLayer(
                    url=tile_url, attribution=name, name=name, visible=False
                )
                self.add_layer(tile_layer)

    # TODO(aimee): if you try and create a histogram for more than one layer, it creates duplicates in the popup
    def create_histograms(self, button_object):
        if self.histogram_layer in self.layers:
            self.remove_layer(self.histogram_layer)
        # TODO(aimee): make this configurable
        minx, maxx = [0, 500]
        plot_args = {"range": (minx, maxx)}
        fig = plt.figure()
        hist_widget = VBox()
        try:
            Histograms.update_selected_data(self)
        except Exception as e:
            return self.error_message(e)
        if len(self.selected_data) == 0:
            return self.error_message("No data or bounding box selected.")
        else:
            for idx, dataset in enumerate(self.selected_data):
                axes = fig.add_subplot(int(f"22{idx+1}"))
                plot_args["ax"] = axes
                # create a histogram
                out = Output()
                with out:
                    out.clear_output()
                    try:
                        dataset.plot.hist(**plot_args)
                    except Exception as err:
                        self.remove_layer(self.loading_widget_layer)
                        self.gen_popup_icon(f"Error: {err}")
                        return
                    axes.set_title(dataset.attrs["title"])
                    display(fig)

        hist_widget.children = [out]
        hist_location = self.bbox_centroid or self.center
        histogram_layer = Popup(
            child=hist_widget, location=hist_location, min_width=500, min_height=300
        )
        self.histogram_layer = histogram_layer
        self.remove_layer(self.loading_widget_layer)
        self.add_layer(histogram_layer)
        return None

    def gen_mosaic_dataset_reader(self, assets, bounds):
        # see https://github.com/cogeotiff/rio-tiler/blob/main/rio_tiler/io/rasterio.py#L368-L380
        def _part_read(src_path: str, *args, **kwargs) -> ImageData:
            with Reader(src_path) as src:
                # src.part((minx, miny, maxx, maxy), **kwargs)
                return src.part(bounds, *args, **kwargs)

        # mosaic_reader will use multithreading to distribute the image fetching
        # and then merge all arrays together
        # Vincent: This will not work if the image do not have the same resolution (because we won't be able to overlay them).
        # If you know the resolution you want to use you can use width=.., height=.. instead of max_size=512 (it will ensure you create the same array size for all the images.
        # change the max_size to make it faster/slower
        # TODO(aimee): make this configurable
        img, _ = mosaic_reader(assets, reader=_part_read, max_size=512)

        # create Masked Array from ImageData
        data = img.as_masked()
        # Avoid non-masked nan/inf values
        numpy.ma.fix_invalid(data, copy=False)
        # TODO(aimee): determine if this might help for creating the histograms quickly
        # hist = {}
        # for ii, b in enumerate(img.count):
        #     h_counts, h_keys = numpy.histogram(data[b].compressed())
        #     hist[f"b{ii + 1}"] = [h_counts.tolist(), h_keys.tolist()]
        return xr.DataArray(data)
