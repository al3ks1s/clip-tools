from clip_tools.utils import read_fmt, write_fmt, write_bytes, read_csp_str, write_csp_str
from clip_tools.clip.Database import Database
import io 
import zlib
import binascii
from attrs import define
from Cryptodome.Hash import MD5
import random
import time
import struct

class Block:
    begin_chunk_signature: str = 'BlockDataBeginChunk'.encode('UTF-16BE')
    end_chunk_signature: str = 'BlockDataEndChunk'.encode('UTF-16BE')
    status_chunk_signature: str = 'BlockStatus'.encode('UTF-16BE')
    checksum_chunk_signature: str = 'BlockCheckSum'.encode('UTF-16BE')

    block_data_index: int
    data_present: int

    data: b''

    def __init__(self, block_data_index, data_present, data):
        self.block_data_index = block_data_index
        self.data_present = data_present
        self.data = data

    @classmethod
    def new(cls, index, data = None):

        if data is None:
            return cls(index, False, data)

        return cls(index, True, data)

    @classmethod
    def read(cls, fp):

        data = None

        block_data_size = read_fmt(">i", fp)
        block_data_text_size = read_fmt(">i", fp) * 2

        signature = fp.read(block_data_text_size)
        assert signature == Block.begin_chunk_signature

        block_data_index = read_fmt(">i", fp)
        #print(block_data_index)
        unk = fp.read(12)
        #print(unk)
        #  Looks like Int:NumChannel,Int:BlockWidth,Int:BlockHeight
        #  Usually b'\x00\x05\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00'

        data_present = read_fmt(">i", fp)
        if data_present:

            subblock_size = read_fmt(">i", fp)
            le_sublock_size = read_fmt('<i', fp)

            assert subblock_size == le_sublock_size + 4 # Why the size twice? Good question

            data = fp.read(le_sublock_size)

        block_end_chunk_size = read_fmt(">i", fp) * 2
        end_signature = fp.read(block_end_chunk_size)
        assert end_signature == Block.end_chunk_signature

        return cls(block_data_index, data_present, data)

    def write(self, fp):

        block_size_offset = fp.tell()
        written = write_fmt(fp, ">i", 0)

        written += write_fmt(fp, ">i", len(Block.begin_chunk_signature) // 2)
        written += write_bytes(fp, Block.begin_chunk_signature)

        written += write_fmt(fp, ">i", self.block_data_index)
        written += write_bytes(fp, b'\x00\x05\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00')
        written += write_fmt(fp, ">i", self.data_present)

        if self.data_present:

            offset = fp.tell()
            written += write_fmt(fp, ">i", 0)
            written += write_fmt(fp, "<i", 0)

            data_written = write_bytes(fp, self.data)
            written += data_written

            fp.seek(offset, 0)
            write_fmt(fp, ">i", data_written + 4)
            write_fmt(fp, "<i", data_written)

            fp.seek(0, 2)

        written += write_fmt(fp, ">i", len(Block.end_chunk_signature) // 2)
        written += write_bytes(fp, Block.end_chunk_signature)

        fp.seek(block_size_offset)
        write_fmt(fp, ">i", written)

        fp.seek(0, 2)

        return written

    def tobytes(self):
        data = io.BytesIO()
        written = self.write(data)
        return written

    def checksum(self):


        if not self.data_present:
            return 0

        # I have no idea what the algorithm is, its not the standard CRC32 algorithm (nor any i derivatives tried)

        return 0

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
    #block_status: list
    #block_checksums: list

    def __len__(self) -> int:
        return self.blocks.__len__()

    def __iter__(self):
        return self.blocks.__iter__()

    def __getitem__(self, key):
        return self.blocks.__getitem__(key)

    def __setitem__(self, key, value) -> None:
        self.blocks.__setitem__(key, value)

    def __delitem__(self, key) -> None:
        self.blocks.__delitem__(key)

    def remove(self, block):
        self.blocks.remove(block)
        return self

    def append(self, block) -> None:
        self.extend([block])

    def extend(self, layers) -> None:
        self.blocks.extend(layers)

    def clear(self) -> None:
        self.blocks.clear()

    def index(self, block) -> int:
        return self.blocks.index(block)

    @classmethod
    def new(cls):
        return cls(
            [],
        )

    @classmethod
    def read(cls, fp):

        blocks = []
        block_status = []
        block_checksums = []

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

            else:
                fp.seek(0)
                return VectorChunk.read(fp)

        return BlockData(blocks) #, block_status, block_checksums)

    def write(self, fp):

        written = 0

        for block in self:
            written += block.write(fp)

        # Writing block status (always 1)
        written += write_fmt(fp, ">i", len(Block.status_chunk_signature) // 2)
        written += write_bytes(fp, Block.status_chunk_signature)

        written += write_fmt(fp, ">i", 12)
        written += write_fmt(fp, ">i", len(self))
        written += write_fmt(fp, ">i", 4)

        for _ in range(len(self)):
            written += write_fmt(fp, ">i", 1)

        # Writing block checksums
        written += write_fmt(fp, ">i", len(Block.checksum_chunk_signature) // 2)
        written += write_bytes(fp, Block.checksum_chunk_signature)

        written += write_fmt(fp, ">i", 12)
        written += write_fmt(fp, ">i", len(self))
        written += write_fmt(fp, ">i", 4)

        for i in range(len(self)):
            written += write_fmt(fp, ">I", self.blocks[i].checksum())
            # Writing 0 for checksum, feel free to search the proper algorithm (its not classic CRC32)

        return written

class DataChunk:

    chunk_signature: str = b'CHNKExta'
    external_chunk_id: str

    block_data: BlockData
    vector_chunk: VectorChunk

    def __init__(self, external_chunk_id, block_data):
        self.external_chunk_id = external_chunk_id
        self.block_data = block_data

    @classmethod
    def new_id(cls):
        mdhasher = MD5.new()
        mdhasher.update(struct.pack(">q", time.time_ns()))
        mdhasher.update(random.randbytes(random.randint(30, 1000)))

        hash_id = mdhasher.hexdigest()

        return ("extrnlid" + hash_id.upper()).encode("UTF-8")

    @classmethod
    def new(cls, extrnlid = None):

        if extrnlid is None:
            extrnlid = cls.new_id()

        return cls(
            extrnlid,
            BlockData.new()
        )

    @classmethod
    def read(cls, fp):

        external_chunk_size = read_fmt(">q", fp)

        external_chunk_id_length = read_fmt(">q", fp)
        external_chunk_id = fp.read(external_chunk_id_length)
        #external_chunk_id = read_csp_str(">q", fp)

        external_chunk_size_2 = read_fmt(">q", fp)

        assert external_chunk_size == external_chunk_size_2 + external_chunk_id_length + 16

        block_raw = io.BytesIO(fp.read(external_chunk_size_2))

        block_datas = BlockData.read(block_raw)

        return cls(external_chunk_id, block_datas)

    def write(self, fp):

        written = write_bytes(fp, DataChunk.chunk_signature)

        size_offset = fp.tell()
        written += write_fmt(fp, ">q", 0)

        #written += write_csp_str(">q", fp, self.external_chunk_id)
        written += write_fmt(fp, ">q", len(self.external_chunk_id))
        written += write_bytes(fp, self.external_chunk_id)

        size2_offset = fp.tell()
        written += write_fmt(fp, ">q", 0)

        data_written = self.block_data.write(fp)
        written += data_written

        fp.seek(size_offset)
        write_fmt(fp, ">q", written - 16)

        fp.seek(size2_offset)
        write_fmt(fp, ">q", written - (len(self.external_chunk_id) + 32))

        fp.seek(0, 2)

        return written

class DataChunks(dict):

    @classmethod
    def new(cls):
        return cls()

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

        written = 0

        for chunk_id in self:
            external_id_offsets.append((chunk_id, fp.tell()))
            written += self[chunk_id].write(fp)

        return external_id_offsets, written