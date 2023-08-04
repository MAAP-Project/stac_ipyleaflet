from stac_ipyleaflet.core import StacIpyleaflet

class Helpers(StacIpyleaflet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def test_this(self):
        print(f'FROM TEST_THIS')