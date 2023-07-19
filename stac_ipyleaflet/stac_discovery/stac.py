# [SOME] code taken from https://github.com/giswqs/leafmap/blob/master/leafmap/stac.py
from pystac_client import ItemSearch
from stac_ipyleaflet.stac_discovery.types import CollectionObj
from stac_ipyleaflet.stac_discovery.requests import make_get_request
import logging

class Stac():

    @staticmethod
    def organize_collections(collections=[]):
        output_collections = []
        for collection in collections:
            try:
                data = collection.to_dict()
                id = data["id"].strip()
                title = data["title"].strip()

                start_date = data["extent"]["temporal"]["interval"][0][0]
                end_date = data["extent"]["temporal"]["interval"][0][1]

                if start_date is not None:
                    start_date = start_date.split("T")[0]
                else:
                    start_date = ""

                if end_date is not None:
                    end_date = end_date.split("T")[0]
                else:
                    end_date = ""

                bbox = ", ".join(
                    [str(coord) for coord in data["extent"]["spatial"]["bbox"][0]]
                )

                metadata = None
                href = None
                for l in data["links"]:
                    if l["rel"] == "about":
                        metadata = l["href"]
                    if l["rel"] == "self":
                        href = l["href"]

                description = (
                    data["description"]
                    .replace("\n", " ")
                    .replace("\r", " ")
                    .replace("\\u", " ")
                    .replace("                 ", " ")
                )

                license = data["license"]
                collection_obj: CollectionObj = CollectionObj({'id': id, 'title': title, 'start_date': start_date, 'end_date': end_date, 'bbox': bbox, 'metadata': metadata, 'href': href, 'description': description, 'license': license})
                output_collections.append(collection_obj)
            except Exception as err:
                error = {'error': err, 'collection': collection}
                logging.error(error)
                return None
        if len(output_collections) > 0:
            output_collections.sort(key= lambda x:x['title'])
        return output_collections

    @staticmethod
    def get_item_info(url=None, **kwargs):
        """Get INFO of a single SpatialTemporal Asset Catalog (STAC) **COG** item.
        Args:
            url (str): HTTP URL to a STAC item
        Returns:
            json: Response with Item info.
        """
        if url is None:
            raise ValueError("Item url must be specified to get stac_bands")

        if isinstance(url, str):
            r = make_get_request(url).json()
            
        return r
    

    @staticmethod
    def stac_tile(
        url=None,
        collection=None,
        item=None,
        assets=None,
        bands=None,
        titiler_stac_endpoint=None,
        **kwargs,
    ):
        """Get a tile layer from a single SpatialTemporal Asset Catalog (STAC) item.
        Args:
            url (str): HTTP URL to a STAC item
            collection (str): STAC collection ID, e.g., landsat-8-c2-l2.
            item (str): STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_stac_endpoint (str, optional): Titiler endpoint, Defaults to None.
        Returns:
            str: Returns the STAC Tile layer URL.
        """
        if url is None and collection is None:
            raise ValueError("Either url or collection must be specified. stac_tile")

        kwargs["rescale"] = "0,50"

        if url is not None:
            kwargs["url"] = url
        if collection is not None:
            kwargs["collection"] = collection
        if item is not None:
            kwargs["item"] = item

        if "palette" in kwargs:
            kwargs["colormap_name"] = kwargs["palette"].lower()
            del kwargs["palette"]

        if isinstance(bands, list) and len(set(bands)) == 1:
            bands = bands[0]

        if isinstance(assets, list) and len(set(assets)) == 1:
            assets = assets[0]

        if isinstance(bands, str):
            bands = bands.split(",")
        if isinstance(assets, str):
            assets = assets.split(",")

        kwargs["assets"] = assets

        TileMatrixSetId = "WebMercatorQuad"
        if "TileMatrixSetId" in kwargs.keys():
            TileMatrixSetId = kwargs["TileMatrixSetId"]
            kwargs.pop("TileMatrixSetId")

        if isinstance(titiler_stac_endpoint, str):
            r = make_get_request(f"{titiler_stac_endpoint}/stac/{TileMatrixSetId}/tilejson.json", kwargs).json()
        else:
            r = make_get_request(titiler_stac_endpoint.url_for_stac_item(), kwargs).json()
        return r["tiles"][0]

    @staticmethod
    def stac_bounds(url=None, collection=None, item=None, titiler_stac_endpoint=None, **kwargs):
        """Get the bounding box of a single SpatialTemporal Asset Catalog (STAC) item.
        Args:
            url (str): HTTP URL to a STAC item
            collection (str): STAC collection ID, e.g., landsat-8-c2-l2.
            item (str): STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            titiler_stac_endpoint (str, optional): Titiler endpoint, Defaults to None.
        Returns:
            list: A list of values representing [left, bottom, right, top]
        """
        if url is None and collection is None:
            raise ValueError("Either url or collection must be specified.")

        if url is not None:
            kwargs["url"] = url
        if collection is not None:
            kwargs["collection"] = collection
        if item is not None:
            kwargs["item"] = item

        if isinstance(titiler_stac_endpoint, str):
            r = make_get_request(f"{titiler_stac_endpoint}/stac/bounds", kwargs).json()
        else:
            r = make_get_request(titiler_stac_endpoint.url_for_stac_bounds(), kwargs).json()

        bounds = r["bounds"]
        return bounds

    # QUESTION: Is this being or planning to be used? 
    def add_stac_layer(
        self,
        url=None,
        collection=None,
        item=None,
        assets=None,
        bands=None,
        titiler_stac_endpoint=None,
        # name="STAC Layer",
        # attribution="",
        # opacity=1.0,
        # shown=True,
        **kwargs,
    ):
        """Adds a STAC TileLayer to the map.
        Args:
            url (str): HTTP URL to a STAC item
            collection (str): STAC collection ID, e.g., landsat-8-c2-l2.
            item (str): STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_stac_endpoint (str, optional): Titiler endpoint, Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """
        tile_url = Stac.stac_tile(
            url, collection, item, assets, bands, titiler_stac_endpoint, **kwargs
        )
        return tile_url
        # bounds = Stac.stac_bounds(url, collection, item, titiler_stac_endpoint)
        # self.add_tile_layer(tile_url, name, attribution, opacity, shown)
        # self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        # if not hasattr(self, "cog_layer_dict"):
        #     self.cog_layer_dict = {}

        # if assets is None and bands is not None:
        #     assets = bands

        # params = {
        #     "url": url,
        #     "collection": collection,
        #     "item": item,
        #     "assets": assets,
        #     "bounds": bounds,
        #     "titiler_stac_endpoint": self.titiler_stac_endpoint,
        #     "type": "STAC",
        # }

        # self.cog_layer_dict[name] = params

    @staticmethod
    def set_default_bands(bands):
        if len(bands) == 0:
            return [None]

        if isinstance(bands, str):
            bands = [bands]

        if len(bands) == 1:
            return bands
        
        if not isinstance(bands, list):
            raise ValueError("bands must be a list or a string.")

    @staticmethod
    def stac_search(
        url,
        method="GET",
        max_items=None,
        limit=100,
        ids=None,
        bbox=None,
        intersects=None,
        datetime=None,
        query=None,
        filter=None,
        filter_lang=None,
        sortby=None,
        fields=None,
        get_info=False,
        **kwargs,
    ):
        if isinstance(intersects, dict) and "geometry" in intersects:
            intersects = intersects["geometry"]

        search = ItemSearch(
            url=url,
            method=method,
            max_items=max_items,
            limit=limit,
            ids=ids,
            bbox=bbox,
            intersects=intersects,
            datetime=datetime,
            query=query,
            filter=filter,
            filter_lang=filter_lang,
            sortby=sortby,
            fields=fields,
        )
        if get_info:
            items = list(search.item_collection())
            info = {}
            for item in items:
                info[item.id] = {'id': item.id, 'href': item.get_self_href(), 'bands': list(item.get_assets().keys()), 'assets': item.get_assets()}
            return info
        else:
            return search
    
    @staticmethod
    def get_metadata(   
        data_type="cog",
        titiler_stac_endpoint=None,
        url=None,
        max_size=None,
        **kwargs,
    ):
        if url is not None:
            kwargs["url"] = url
        if max_size is not None:
            kwargs["max_size"] = max_size

        if isinstance(titiler_stac_endpoint, str):
            r = make_get_request(f"{titiler_stac_endpoint}/{data_type}/metadata", kwargs).json()
            return r
        else:
            return "Cannot process request: titiler stac endpoint not provided."

    @staticmethod
    def get_tile_url(
        data_type="cog",
        url=None,
        collection=None,
        item=None,
        assets=None,
        bands=None,
        palette=None,
        titiler_stac_endpoint=None,
        **kwargs,
    ):
        """Get a tile layer url from a single SpatialTemporal Asset Catalog (STAC) item.
        Args:
            url (str): HTTP URL to a STAC item
            collection (str): STAC collection ID, e.g., landsat-8-c2-l2.
            item (str): STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_stac_endpoint (str, optional): Titiler endpoint, Defaults to None.
        Returns:
            str: Returns the STAC Tile layer URL.
        """
        if url is None and collection is None:
            raise ValueError("Either url or collection must be specified. stac_tile")

        kwargs["rescale"] = "0,50"

        if url is not None:
            kwargs["url"] = url
        if collection is not None:
            kwargs["collection"] = collection
        if item is not None:
            kwargs["item"] = item

        if palette is not None:
            # kwargs["colormap_name"] = kwargs["palette"].lower()
            kwargs["colormap_name"] = palette
            # del kwargs["palette"]

        if isinstance(bands, list) and len(set(bands)) == 1:
            bands = bands[0]

        if isinstance(assets, list) and len(set(assets)) == 1:
            assets = assets[0]

        if isinstance(bands, str):
            bands = bands.split(",")
        if isinstance(assets, str):
            assets = assets.split(",")

        kwargs["assets"] = assets

        TileMatrixSetId = "WebMercatorQuad"
        if "TileMatrixSetId" in kwargs.keys():
            TileMatrixSetId = kwargs["TileMatrixSetId"]
            kwargs.pop("TileMatrixSetId")

        if isinstance(titiler_stac_endpoint, str):
            r = make_get_request(f"{titiler_stac_endpoint}/{data_type}/{TileMatrixSetId}/tilejson.json", kwargs).json()
            return r
        else:
            return "STAC ENDPOINT IS NECESSARY."