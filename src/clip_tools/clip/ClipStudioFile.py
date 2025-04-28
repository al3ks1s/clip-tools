
from clip_tools.clip.ChunkHeader import ChunkHeader
from clip_tools.clip.DataChunk import DataChunks
from clip_tools.clip.Database import Database
from clip_tools.clip.Footer import Footer

from clip_tools.utils import read_fmt, write_fmt

class ClipStudioFile:

    chunk_signature: str = b'CSFCHUNK'
    file_size: int
    header_offset: int

    header: ChunkHeader
    data_chunks: DataChunks
    sql_database: Database
    footer: Footer

    def __init__(self, header, data_chunks, sql_database):
        self.header = header
        self.data_chunks = data_chunks
        self.sql_database = sql_database

    @classmethod
    def new(cls):
        return cls(
            ChunkHeader.new(),
            DataChunks.new(),
            Database.new()
        )

    @classmethod
    def read(cls, fp):

        assert ClipStudioFile.chunk_signature == fp.read(8)
        file_size = read_fmt(">q", fp)
        header_offset = read_fmt(">q", fp)

        header = ChunkHeader.read(fp)
        data_chunks = DataChunks.read(fp)
        sql_database = Database.read(fp)
        footer = Footer.read(fp)

        return cls(header, data_chunks, sql_database)

    def write(self, fp):

        fp.write(ClipStudioFile.chunk_signature)
        size_ptr = fp.tell()
        write_fmt(fp, ">q", 0)
        write_fmt(fp, ">q", 24)

        self.header.write(fp)
        ext_id_offsets, _ = self.data_chunks.write(fp)

        # Write the db address to the header
        db_offset = fp.tell()
        fp.seek(0x30)
        write_fmt(fp, ">q", db_offset)
        fp.seek(db_offset)

        self.sql_database.write(fp, ext_id_offsets)
        Footer.write(fp)

        file_size = fp.tell()
        fp.seek(size_ptr, 0)
        write_fmt(fp, ">q", file_size)
