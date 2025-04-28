import logging
import struct

import attrs

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
    if str_size is None:
        return None
    string_data = f.read(2 * str_size)
    return string_data.decode('UTF-16-BE')

def read_csp_unicode_le_str(size_fmt, f):
    str_size = read_fmt(size_fmt, f)
    if str_size is None:
        return None
    string_data = f.read(2 * str_size)
    return string_data.decode('UTF-16-LE')

def read_csp_str(size_fmt, f):
    str_size = read_fmt(size_fmt, f)
    if str_size is None:
        return None
    string_data = f.read(str_size)
    return string_data.decode('UTF-8')

def write_csp_unicode_str(size_fmt, f, string_data):

    str_to_write = string_data.encode('UTF-16-BE')
    written = write_fmt(f, size_fmt, len(str_to_write) // 2)
    written += write_bytes(f, str_to_write)

    if written != len(str_to_write) + struct.calcsize(size_fmt):
        raise IOError(
            "Failed to write data: written=%d, expected=%d." % (written, len(str_to_write) + struct.calcsize(size_fmt))
        )

    return written

def write_csp_unicode_le_str(size_fmt, f, string_data):

    str_to_write = string_data.encode('UTF-16-LE')
    written = write_fmt(f, size_fmt, len(str_to_write) // 2)
    written += write_bytes(f, str_to_write)

    if written != len(str_to_write) + struct.calcsize(size_fmt):
        raise IOError(
            "Failed to write data: written=%d, expected=%d." % (written, len(str_to_write) + struct.calcsize(size_fmt))
        )

    return written

def write_csp_str(size_fmt, f, string_data):

    str_to_write = string_data.encode('UTF-8')
    written = write_fmt(f, size_fmt, len(str_to_write))
    written += write_bytes(f, str_to_write)

    if written != len(str_to_write) + struct.calcsize(size_fmt):
        raise IOError(
            "Failed to write data: written=%d, expected=%d." % (written, len(str_to_write) + struct.calcsize(size_fmt))
        )

    return written


def pack(fmt, *args):
    fmt = str(">" + fmt)
    return struct.pack(fmt, *args)

def unpack(fmt, data):
    fmt = str(">" + fmt)
    return struct.unpack(fmt, data)

def decompositor(x):
    powers = []
    i = 1
    while i <= x:
        if i & x:
            powers.append(str(i))
        i <<= 1
    return powers

def shifter_calculator(fmt):
    return (struct.calcsize(fmt) - 1) * 8

def channel_to_pil(c_num):

    return {
        3: "RGB",
        4: "RGBA",
        5: "RGBA",

        1: "L",
        2: "LA"
    }.get(c_num)

def get_pil_depth(pil_mode: str) -> int:
    """Get the depth of image for PIL modes."""
    return {
        "1": 1,
        "L": 8,
        "LA": 8,
        "RGB": 32,
        "RGBA": 32,
    }.get(pil_mode)

def pil_to_channel(pil_mode):

    return {
        "RGB": 4,
        "RGBA": 4,

        "L": 1,
        "LA": 1,

        "1": 1
    }.get(pil_mode)

# Attrs converters
def validate_range(value, field):

    range_ = field.metadata["range"]
    return min(max(value, range_[0]), range_[1])

def attrs_range_builder(type_, default, range_):
    return attrs.field(
        validator=attrs.validators.instance_of(type_),
        default=default,
        metadata={"range": range_},
        converter=[
            attrs.Converter(
                validate_range,
                takes_field=True
            )
        ]
    )
