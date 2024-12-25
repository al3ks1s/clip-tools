from clip_tools.parsers import parse_effect_info
from attrs import define
from clip_tools.data_classes import Position, Color, ColorStop, CurvePoint, EffectTone, EffectEdge, Posterization, EffectApplyOpacity, EffectTonePosterize, EffectWaterEdge, EffectLine


@define
class LayerEffects():
    
    edge: EffectEdge
    tone: EffectTone
    apply_opacity: EffectApplyOpacity
    posterize: EffectTonePosterize
    water_edge: EffectWaterEdge
    line_extract: EffectLine

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, layer_effect_info):
        layer_infos = parse_effect_info(layer_effect_info)
        return cls(layer_infos["EffectEdge"],
                    layer_infos["EffectTone"],
                    layer_infos["EffectApplyOpacity"],
                    layer_infos["EffectTonePosterize"],
                    layer_infos["EffectWaterEdge"],
                    layer_infos["EffectLine"])

    @classmethod
    def new(cls, effects):
        pass