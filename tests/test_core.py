from ipyleaflet import Map
from stac_ipyleaflet.core import StacIpyleaflet

test_map_instance = StacIpyleaflet()


def test_create_buttons_layout():
    buttons_container = StacIpyleaflet.create_buttons_layout(test_map_instance)
    button_descriptions = [item.description for item in buttons_container.children]
    assert len(buttons_container.children) == 3
    assert button_descriptions == ["Interact", "Layers", "STAC Data"]
