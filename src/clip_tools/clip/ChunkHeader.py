from clip_tools.utils import read_fmt


class ChunkHeader:
    
    chunk_signature: str = b'CHNKHead'

    header_size: int
    header_data: str
    # Unknown data afterward
    
    def __init__(self, header_size, header_data):
        self.header_size = header_size
        self.header_data = header_data

    @classmethod
    def read(cls, fp):
        
        assert fp.read(8) == ChunkHeader.chunk_signature

        header_size = read_fmt(">q", fp)

        header_data = fp.read(header_size)

        return cls(header_size, header_data)