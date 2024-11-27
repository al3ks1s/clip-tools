
from clip_tools.clip.ChunkHeader import ChunkHeader
from clip_tools.clip.DataChunk import DataChunks
from clip_tools.clip.Database import Database
from clip_tools.clip.Footer import Footer

from clip_tools.utils import read_fmt

class ClipStudioFile:
    
    chunk_signature: str = b'CSFCHUNK'
    file_size: int
    header_offset: int

    header: ChunkHeader
    data_chunks: DataChunks
    sql_database: Database
    footer: Footer

    def __init__(self, file_size, header_offset, header, data_chunks, sql_database):
        self.file_size = file_size
        self.header_offset = header_offset
        self.header = header
        self.data_chunks = data_chunks
        self.sql_database = sql_database

    @classmethod
    def read(cls, fp):

        assert ClipStudioFile.chunk_signature == fp.read(8)
        file_size = read_fmt(">q", fp)[0]
        header_offset = read_fmt(">q", fp)[0]

        header = ChunkHeader.read(fp)
        data_chunks = DataChunks.read(fp)
        sql_database = Database.read(fp)
        footer = Footer.read(fp)

        return cls(file_size, header_offset, header, data_chunks, sql_database)
