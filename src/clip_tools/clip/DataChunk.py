from clip_tools.utils import read_fmt, write_fmt, write_bytes
from clip_tools.clip.Database import Database
import io 
import zlib
import binascii
from attrs import define

class Block:
    begin_chunk_signature: str = 'BlockDataBeginChunk'.encode('UTF-16BE')
    end_chunk_signature: str = 'BlockDataEndChunk'.encode('UTF-16BE')
    status_chunk_signature: str = 'BlockStatus'.encode('UTF-16BE')
    checksum_chunk_signature: str = 'BlockCheckSum'.encode('UTF-16BE')

    block_data_size: int
    block_data_text_size: int

    block_data_index: int

    data_present: int

    data: b''

    def __init__(self, block_data_size, block_data_text_size, block_data_index, data_present, data):
        self.block_data_size = block_data_size
        self.block_data_text_size = block_data_text_size
        self.block_data_index = block_data_index
        self.data_present = data_present
        self.data = data

    @classmethod
    def read(cls, fp):

        data = None

        block_data_size = read_fmt(">i", fp)
        block_data_text_size = read_fmt(">i", fp) * 2

        signature = fp.read(block_data_text_size)
        assert signature == Block.begin_chunk_signature

        block_data_index = read_fmt(">i", fp)

        unk = fp.read(12)
        # Usually b'\x00\x05\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00'

        data_present = read_fmt(">i", fp)

        if data_present:
            subblock_size = read_fmt(">i", fp)
            le_sublock_size = read_fmt('<i', fp)

            assert subblock_size == le_sublock_size + 4 # Why the size twice? Good question

            data = fp.read(le_sublock_size)

        block_end_chunk_size = read_fmt(">i", fp) * 2
        end_signature = fp.read(block_end_chunk_size)
        assert end_signature == Block.end_chunk_signature

        return cls(block_data_size, block_data_text_size, block_data_index, data_present, data)

    def write(self, fp):

        block_size_offset = fp.tell()
        write_fmt(fp, ">i", 0)

        write_fmt(fp, ">i", len(Block.begin_chunk_signature) // 2)
        fp.write(Block.begin_chunk_signature)

        write_fmt(fp, ">i", self.block_data_index)
        write_bytes(fp, b'\x00\x05\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00')
        write_fmt(fp, ">i", self.data_present)

        if self.data_present:

            offset = fp.tell()
            write_fmt(fp, ">i", 0)
            write_fmt(fp, "<i", 0)

            written = write_bytes(fp, self.data)

            fp.seek(offset, 0)
            write_fmt(fp, ">i", written + 4)
            write_fmt(fp, "<i", written)

            fp.seek(0, 2)

        write_fmt(fp, ">i", len(Block.end_chunk_signature) // 2)
        fp.write(Block.end_chunk_signature)

        end_offset = fp.tell()
        fp.seek(block_size_offset)
        write_fmt(fp, ">i", end_offset - block_size_offset)

        fp.seek(0, 2)

    def checksum(self):

        if not self.data_present:
            return 0

        return -1

@define
class VectorChunk():

    data: bytes

    @classmethod
    def read(cls, fp):
        return cls(fp.read())

    def write(self, fp):
        return write_bytes(fp, self.data)

@define
class BlockData():

    blocks: list
    block_status: list
    block_checksums: list

    @classmethod
    def read(cls, fp):

        blocks = []
        block_status = []
        block_checksums = []

        has_next_block = True

        while fp.tell() < fp.getbuffer().nbytes:

            block_data_size = read_fmt(">i", fp)

            if block_data_size == 11 or block_data_size == 13: # Block Status or Block checksum
                signature = signature = fp.read(block_data_size * 2)

            else:
                block_data_text_size = read_fmt(">i", fp) * 2
                signature = fp.read(block_data_text_size)

            if signature == Block.begin_chunk_signature:

                fp.seek(-8 - block_data_text_size , 1)

                block = Block.read(fp)
                blocks.append(block)

            elif signature == Block.status_chunk_signature:

                unknown_var = read_fmt(">i", fp) # Need to find out what this is, usually 0c
                assert unknown_var == 12

                block_count = read_fmt(">i", fp)

                unknown_var2 = read_fmt(">i", fp)
                assert unknown_var2 == 4

                assert block_count == len(blocks)

                for i in range(block_count):
                    a = read_fmt(">i", fp)
                    block_status.append(a)

            elif signature == Block.checksum_chunk_signature:

                unknown_var3 = read_fmt(">i", fp) # Need to find out what this is, usually 0c
                assert unknown_var3 == 12

                block_count = read_fmt(">i", fp)

                unknown_var4 = read_fmt(">i", fp)
                assert unknown_var4 == 4

                assert block_count == len(blocks)

                for i in range(block_count):
                    a = read_fmt(">I", fp)
                    block_checksums.append(a)

                    if blocks[i].data_present:
                        blocks[i].checksum()
                        #print(hex(a))
                        #print()

                #print(block_count)
                #print(block_checksums)
                #print()

            else:
                fp.seek(0)
                return VectorChunk.read(fp)

        return BlockData(blocks, block_status, block_checksums)

    def write(self, fp):

        for block in self.blocks:
            block.write(fp)

        # Writing block status (always 1)
        write_fmt(fp, ">i", len(Block.status_chunk_signature) // 2)
        fp.write(Block.status_chunk_signature)

        write_fmt(fp, ">i", 12)
        write_fmt(fp, ">i", len(self.blocks))
        write_fmt(fp, ">i", 4)

        for _ in range(len(self.blocks)):
            write_fmt(fp, ">i", 1)

        # Writing block checksums
        write_fmt(fp, ">i", len(Block.checksum_chunk_signature) // 2)
        fp.write(Block.checksum_chunk_signature)

        write_fmt(fp, ">i", 12)
        write_fmt(fp, ">i", len(self.blocks))
        write_fmt(fp, ">i", 4)

        for i in range(len(self.blocks)):
            write_fmt(fp, ">I", self.block_checksums[i])

class DataChunk:

    chunk_signature: str = b'CHNKExta'
    external_chunk_size: int
    external_chunk_id: str

    block_data: BlockData
    vector_chunk: VectorChunk

    def __init__(self, external_chunk_size, external_chunk_id, block_datas):
        self.external_chunk_size = external_chunk_size
        self.external_chunk_id = external_chunk_id
        self.block_datas = block_datas

    @classmethod
    def read(cls, fp):

        external_chunk_size = read_fmt(">q", fp)

        external_chunk_id_length = read_fmt(">q", fp)
        external_chunk_id = fp.read(external_chunk_id_length)

        external_chunk_size_2 = read_fmt(">q", fp)

        assert external_chunk_size == external_chunk_size_2 + external_chunk_id_length + 16

        block_raw = io.BytesIO(fp.read(external_chunk_size_2))

        block_datas = BlockData.read(block_raw)

        return cls(external_chunk_size, external_chunk_id, block_datas)

    def write(self, fp):

        fp.write(DataChunk.chunk_signature)

        size_offset = fp.tell()
        write_fmt(fp, ">q", 0)

        write_fmt(fp, ">q", len(self.external_chunk_id))
        fp.write(self.external_chunk_id)

        size2_offset = fp.tell()
        write_fmt(fp, ">q", 0)

        self.block_datas.write(fp)

        block_size = fp.tell() - size_offset

        fp.seek(size_offset)
        write_fmt(fp, ">q", block_size - 8)

        fp.seek(size2_offset)
        write_fmt(fp, ">q", block_size - (len(self.external_chunk_id) + 16) - 8)

        fp.seek(0, 2)

class DataChunks(dict):

    @classmethod
    def read(cls, fp): # chunkSizes

        chunks = DataChunks()

        while True:

            signature = fp.read(8)
            if signature == DataChunk.chunk_signature:
                chunk = DataChunk.read(fp)
            elif signature == Database.chunk_signature:
                fp.seek(-8, 1)
                break

            chunks[chunk.external_chunk_id] = chunk

        return chunks

    def write(self, fp):

        external_id_offsets = []

        for chunk_id in self:
            external_id_offsets.append((chunk_id, fp.tell()))
            self[chunk_id].write(fp)

        return external_id_offsets