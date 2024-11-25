class Footer:
    
    chunk_signature = b'CHNKFoot'

    @classmethod
    def read(cls, fp):
        
        assert fp.read(8) == Footer.chunk_signature
    
    @classmethod
    def write(cls, fp):
        fp.write(Footer.chunk_signature)