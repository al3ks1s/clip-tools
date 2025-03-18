class Footer:
    
    chunk_signature = b'CHNKFoot'

    @classmethod
    def read(cls, fp):
        
        assert fp.read(8) == Footer.chunk_signature
        footer_data = fp.read(8) # 8 0x00
        #print(footer_data)

    @classmethod
    def write(cls, fp):
        fp.write(Footer.chunk_signature)
        fp.write(8*b'\x00')