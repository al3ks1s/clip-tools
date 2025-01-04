from attrs import define
from clip_tools.parsers import decode_chunk_to_pil, parse_offscreen_attribute

@define
class Mask():

    layer: None
    masking_mode: int
    offscreen: bytes

    def topil(self):

        chunk = self.layer.clip_file.data_chunks[self.offscreen.BlockData]

        parsed_attribute = parse_offscreen_attribute(self.offscreen.Attribute)

        return decode_chunk_to_pil(chunk, parsed_attribute)

    @classmethod
    def from_pil(cls):
        pass

    