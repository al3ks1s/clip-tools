from clip_tools.utils import read_fmt, write_fmt
import io
from attrs import define


class ChunkHeader:

    chunk_signature: str = b'CHNKHead'

    @classmethod
    def new(cls):
        return cls()

    @classmethod
    def read(cls, fp):

        assert fp.read(8) == ChunkHeader.chunk_signature

        header_size = read_fmt(">q", fp)
        # To investigate

        assert read_fmt(">q", fp) == 256
        database_offset = read_fmt(">q", fp)
        assert read_fmt(">q", fp) == 16

        header_data = fp.read(16) # Unknown yet irrelevant data

        return cls()

    def write(self, fp):

        fp.write(ChunkHeader.chunk_signature)
        write_fmt(fp, ">q", 40)
        write_fmt(fp, ">q", 256)
        write_fmt(fp, ">q", 0) # Will be rewriten with the db address
        write_fmt(fp, ">q", 16)
        fp.write(b'\x00'*16)
