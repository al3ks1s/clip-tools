from clip_tools.utils import read_fmt
from clip_tools.clip.Database import Database

class BlockData:
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

        block_data_size = read_fmt(">i", fp)[0]  
        block_data_text_size = read_fmt(">i", fp)[0] * 2
        
        signature = fp.read(block_data_text_size)

        block_data_index = read_fmt(">i", fp)[0]

        fp.read(12) #????

        data_present = read_fmt(">i", fp)[0]

        if data_present:
            subblock_size = read_fmt(">i", fp)[0]
            le_sublock_size = read_fmt('<i', fp)[0]

            assert subblock_size == le_sublock_size + 4 # Why the size twice? Good question

            data = fp.read(le_sublock_size)

        block_end_chunk_size = read_fmt(">i", fp)[0] * 2
        end_signature = fp.read(block_end_chunk_size)
        assert end_signature == BlockData.end_chunk_signature

        return cls(block_data_size, block_data_text_size, block_data_index, data_present, data)

class BlockDatas(list):
    
    block_status = []
    block_checksums = []

    @classmethod
    def read(cls, fp):
        
        has_next_block = True
        blocks = BlockDatas()

        while has_next_block:

            block_data_size = read_fmt(">i", fp)[0]

            if block_data_size == 11 or block_data_size == 13: # Block Status or Block checksum
                signature = signature = fp.read(block_data_size * 2)
            else:
                block_data_text_size = read_fmt(">i", fp)[0] * 2
                signature = fp.read(block_data_text_size)

            if signature == BlockData.begin_chunk_signature: 

                fp.seek(-8 - block_data_text_size , 1)

                block = BlockData.read(fp)
                blocks.append(block)

            elif signature == BlockData.status_chunk_signature:

                unknown_var = read_fmt(">i", fp)[0] # Need to find out what this is, usually 0c
                block_count = read_fmt(">i", fp)[0]
                unknown_var2 = read_fmt(">i", fp)[0] # Looks like the block count a second time

                assert block_count == len(blocks)
                print(unknown_var2)

                for i in range(block_count):
                    blocks.block_status.append(read_fmt(">i", fp)[0])  
        
            elif signature == BlockData.checksum_chunk_signature:

                unknown_var3 = read_fmt(">i", fp)[0] # Need to find out what this is, usually 0c
                
                block_count = read_fmt(">i", fp)[0]
                unknown_var4 = read_fmt(">i", fp)[0] # Looks like the block count a second time

                assert block_count == len(blocks)
                
                for i in range(block_count):
                    blocks.block_checksums.append(read_fmt(">i", fp)[0])
                
                has_next_block = False
            else:
                pass

        return blocks


class DataChunk:
    
    chunk_signature: str = b'CHNKExta'
    external_chunk_size: int
    external_chunk_id_length:int

    external_chunk_id: str

    block_datas: BlockDatas

    def __init__(self, external_chunk_size, external_chunk_id, block_datas):
        self.external_chunk_size = external_chunk_size
        self.external_chunk_id = external_chunk_id
        self.block_datas = block_datas

    @classmethod
    def read(cls, fp):
        
        external_chunk_size = read_fmt(">q", fp)[0]
        external_chunk_id_length = read_fmt(">q", fp)[0]

        external_chunk_id = fp.read(external_chunk_id_length)

        external_chunk_size_2 = read_fmt(">q", fp)[0]

        assert external_chunk_size == external_chunk_size_2 + external_chunk_id_length + 16

        block_datas = BlockDatas.read(fp)        

        return cls(external_chunk_size, external_chunk_id, block_datas)

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

