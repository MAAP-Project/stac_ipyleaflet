from stac_ipyleaflet.core import StacIpyleaflet


# UI TEST CASES
def test_create_buttons_layout():
    test_map_instance = StacIpyleaflet()
    buttons_container = StacIpyleaflet.create_buttons_layout(test_map_instance)
    button_descriptions = [item.description for item in buttons_container.children]
    assert len(buttons_container.children) == 3
    assert button_descriptions == ["Interact", "Layers", "STAC Data"]


# DRAW CONTROL TEST CASES
def test_remove_draw_controls():
    test_map_instance = StacIpyleaflet()
    test_map_instance.add_control(test_map_instance.point_control)
    test_map_instance.point_control_added = True
    list_of_controls = list(map(lambda x: str(type(x)), test_map_instance.controls))
    assert "<class 'ipyleaflet.leaflet.DrawControl'>" in list_of_controls

    test_map_instance = StacIpyleaflet.remove_draw_controls(test_map_instance)
    list_of_controls = list(map(lambda x: str(type(x)), test_map_instance.controls))
    assert "<class 'ipyleaflet.leaflet.DrawControl'>" not in list_of_controls


# LAYERS TEST CASES
def test_layers():
    test_map_instance = StacIpyleaflet()

    def test_add_biomass_layers_options():
        all_layer_names = [layer.name for layer in test_map_instance.layers]
        assert len(test_map_instance.layers) == 21
        assert "CCI Biomass" in all_layer_names
        assert "NCEO Africa" in all_layer_names

    def test_create_layers_widget():
        # Changing checkbox value to True for layer should add to the applied_layers list
        # @NOTE: Extremely fragile, possibly come to revisit to figure out better way to test
        test_map_instance.controls[2].widget.children[0].children[0].children[
            0
        ].children[0].children[0].children[0].value = True
        assert len(test_map_instance.applied_layers) == 1
        assert test_map_instance.applied_layers[0].name == "CCI Biomass"

    test_add_biomass_layers_options()
    test_create_layers_widget()
