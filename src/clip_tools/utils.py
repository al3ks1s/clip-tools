import logging
import struct


def read_fmt(fmt, fp):
    """
    Reads data from ``fp`` according to ``fmt``.
    """
    #fmt = str(">" + fmt)
    fmt_size = struct.calcsize(fmt)
    data = fp.read(fmt_size)
    if len(data) != fmt_size:
        fp.seek(-len(data), 1)
        raise IOError(
            "Failed to read data section: read=%d, expected=%d. "
            "Likely the file is corrupted." % (len(data), fmt_size)
        )
    return struct.unpack(fmt, data)

def pack(fmt, *args):
    fmt = str(">" + fmt)
    return struct.pack(fmt, *args)

def unpack(fmt, data):
    fmt = str(">" + fmt)
    return struct.unpack(fmt, data)