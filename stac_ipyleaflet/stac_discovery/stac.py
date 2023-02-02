from pystac_client import ItemSearch
from typing import Any, Dict
import json

class Stac():
    def stac_search(
        url,
        method="GET",
        max_items=None,
        limit=100,
        ids=None,
        # collections=None,
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
