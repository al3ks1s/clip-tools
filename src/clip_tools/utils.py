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
    return struct.unpack(fmt, data)[0]


def write_fmt(fp, fmt, *args):
    """
    Writes data to ``fp`` according to ``fmt``.
    """
    #fmt = str(">" + fmt)
    fmt_size = struct.calcsize(fmt)
    written = write_bytes(fp, struct.pack(fmt, *args))
    if written != fmt_size:
        raise IOError(
            "Failed to write data section: written=%d, expected=%d."
            % (written, fmt_size)
        )
    return written


def write_bytes(fp, data):
    """
    Write bytes to the file object and returns bytes written.

    :return: written byte size
    """
    pos = fp.tell()
    fp.write(data)
    written = fp.tell() - pos
    if written != len(data):
        raise IOError(
            "Failed to write data: written=%d, expected=%d." % (written, len(data))
        )
    return written

def read_csp_unicode_str(size_fmt, f):
    str_size = read_fmt(size_fmt, f)  
    if str_size == None:
        return None
    string_data = f.read(2 * str_size)
    return string_data.decode('UTF-16-BE')

def pack(fmt, *args):
    fmt = str(">" + fmt)
    return struct.pack(fmt, *args)

def unpack(fmt, data):
    fmt = str(">" + fmt)
    return struct.unpack(fmt, data)