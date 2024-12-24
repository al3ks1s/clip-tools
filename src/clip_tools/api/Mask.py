from attrs import define

@define
class Mask():
    
    masking_mode: int
    data: bytes

    @classmethod
    def from_bytes(cls, chunk, offscreen_attribute):
        pass