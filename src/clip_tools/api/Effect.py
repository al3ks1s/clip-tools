from clip_tools.parsers import parse_effect_info

class LayerEffect():
    
    def __init__(self, effect_data):

        self.effect_data = effect_data

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, layer_effect_info):
        layer_infos = parse_effect_info(layer_effect_info)

        return cls(layer_infos)