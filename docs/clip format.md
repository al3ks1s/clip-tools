# Clip format

# clip File memo * ``CSFCHUNK``, ``CHNK????`` are 8-byte identification strings.
* The number following the identification string is a big-endian unsigned 64-bit integer.
* The external data of CHNKExta, the chunks it contains, and the block data inside it have a repeating structure.

## Overall structure | Number of bytes | Contents | Description |
|---|---|---|
| 8 | "CSFCHUNK" | File information chunk identification string |
| 8 | integer | file size |
| 8 | Integer? | Fixed to 24 with starting offset of CHNKHead? |
| |
| 8 | "CHNKHead" | Header chunk identification string |
| 8 | Integer | CHNKHead Header information size fixed at 40? |
| 40? | Header information | I don't know the contents |
| |
| 8 | "CHNKExta" | External data chunk identification string |
| 8 | Integer | External data size |
| 8 | Integer | extrnlid + id string length fixed at 40? |
| 40 | String | External data id string (extrnlid...)|
| - | Data | Block data |
| |
| ... | ... | CHNKExta Chunk Repeat |
| |
| 8 | "CHNKSQLi" | SQLite chunk identification string |
| 8 | Integer | SQLite3 database size |
| - | SQLite3 data | |
| |
| 8 | "CHNKFoot" | Footer chunk identification string |
| 8 | Integer | Footer size Is the footer content empty and fixed at 0? |

## Block data structure * BlockData position is also recorded in sqlite Offsets * Only BlockDataBeginChunk has a 4-byte uint at the beginning that represents the size.
* Integer is a big-endian 32-bit unsigned integer * Repeating BlockDataBeginChunk, data, BlockDataEndChunk, then BlockStatus, and finally ending with BlockCheckSum.

### BlockDataBeginChunk
| Number of bytes | Contents | Description |
|---|---|---|
| 4 | Integer | Size of BlockDataBeginChunk (including itself). |
| 4 | Integer | String length(19) |
| - | Variable length 2-byte string | 'BlockDataBeginChunk' |
| 4 | Integer | Block data index |
| 12 | ? |? |
| 4 | Integer | 1 if data is present, 0 if empty. |
| - | Block data | |

### BlockDataEndChunk
| Number of bytes | Contents | Description |
|---|---|---|
| 4 | Integer | String length(17) |
| - | Variable length 2-byte string | 'BlockDataEndChunk' |

### BlockStatus BlockCheckSum
| Number of bytes | Contents | Description |
|---|---|---|
| 4 | Integer | String length |
| - | Variable length 2-byte string | 'BlockStatus' 'BlockCheckSum' |
| 28 | ? |? |

# Notes, etc.* If you only modify the SQLite database, modify the file size of ``CSFCHUNK`` and the database size of ``CHNKSQLi``.
* Offset information of external data is also recorded in the SQLite database, so if the length of the external data changes, also modify Offsets in the SQLite database.
* Layer thumbnail images are not external data but are stored as png files in the SQLite database.
*Not fully verified yet. I added a ? to parts that were not clear.
 