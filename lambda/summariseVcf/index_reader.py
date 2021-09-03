from gzip import GzipFile


class Csi:
    def __init__(self, file_obj):
        with GzipFile(mode='rb', fileobj=file_obj) as stream:
            assert stream.read(4) == b'CSI\x01'
            self.min_shift = get_int32(stream)
            self.depth = get_int32(stream)
            self.bin_limit = ((1 << ((self.depth + 1) * 3)) - 1) / 7
            self.l_aux = get_int32(stream)
            # Note that this aux data is in TBI format.
            # As far as I can tell, this is by convention only, but bcftools will break without it
            # We only use it to get names.
            self.format = get_int32(stream)
            self.col_seq = get_int32(stream)
            self.col_beg = get_int32(stream)
            self.col_end = get_int32(stream)
            self.meta = get_int32(stream)
            self.skip = get_int32(stream)
            self.l_nm = get_int32(stream)
            self.names = []
            last_name = ''
            for _ in range(self.l_nm):
                char = get_char(stream)
                if char != '\x00':
                    last_name += char
                else:
                    self.names.append(last_name)
                    last_name = ''
            self.n_ref = get_int32(stream)
            self.refs = [
                {
                    'n_bin': (n_bin := get_int32(stream)),
                    'bins': [
                        {
                            'bin': get_uint32(stream),
                            'loffset': get_uint64(stream),
                            'n_chunk': (n_chunk := get_int32(stream)),
                            'chunks': [
                                {
                                    'chunk_beg': {
                                        'virtual_file_offset': (virtual := get_uint64(stream)),
                                        'block_offset': virtual >> 16,
                                        'uncompressed_offset': virtual & 65535,
                                    },
                                    'chunk_end': {
                                        'virtual_file_offset': (virtual := get_uint64(stream)),
                                        'block_offset': virtual >> 16,
                                        'uncompressed_offset': virtual & 65535,
                                    },
                                }
                                for _ in range(n_chunk)
                            ],
                        }
                        for _ in range(n_bin)
                    ],
                }
                for _ in range(self.n_ref)
            ]
            self.remainder = stream.read()


class Tbi:
    def __init__(self, file_obj):
        with GzipFile(mode='rb', fileobj=file_obj) as stream:
            assert stream.read(4) == b'TBI\x01'
            self.bin_limit = ((1 << 18) - 1) / 7
            self.n_ref = get_int32(stream)
            self.format = get_int32(stream)
            self.col_seq = get_int32(stream)
            self.col_beg = get_int32(stream)
            self.col_end = get_int32(stream)
            self.meta = get_int32(stream)
            self.skip = get_int32(stream)
            self.l_nm = get_int32(stream)
            self.names = []
            last_name = ''
            for _ in range(self.l_nm):
                char = get_char(stream)
                if char != '\x00':
                    last_name += char
                else:
                    self.names.append(last_name)
                    last_name = ''
            self.refs = [
                {
                    'n_bin': (n_bin := get_int32(stream)),
                    'bins': [
                        {
                            'bin': get_uint32(stream),
                            'n_chunk': (n_chunk := get_int32(stream)),
                            'chunks': [
                                {
                                    'chunk_beg': {
                                        'virtual_file_offset': (virtual := get_uint64(stream)),
                                        'block_offset': virtual >> 16,
                                        'uncompressed_offset': virtual & 65535,
                                    },
                                    'chunk_end': {
                                        'virtual_file_offset': (virtual := get_uint64(stream)),
                                        'block_offset': virtual >> 16,
                                        'uncompressed_offset': virtual & 65535,
                                    },
                                }
                                for _ in range(n_chunk)
                            ],
                        }
                        for _ in range(n_bin)
                    ],
                    'n_intv': (n_intv := get_int32(stream)),
                    'intvs': [
                        {
                            'ioff': {
                                'virtual_file_offset': (virtual := get_uint64(stream)),
                                'block_offset': virtual >> 16,
                                'uncompressed_offset': virtual & 65535,
                            },
                        }
                        for _ in range(n_intv)
                    ]
                }
                for _ in range(self.n_ref)
            ]
            self.remainder = stream.read()


def get_char(stream):
    return chr(int.from_bytes(stream.read(1), byteorder='little', signed=False))


def get_uint16(stream):
    return int.from_bytes(stream.read(2), byteorder='little', signed=False)


def get_int32(stream):
    return int.from_bytes(stream.read(4), byteorder='little', signed=True)


def get_uint32(stream):
    return int.from_bytes(stream.read(4), byteorder='little', signed=False)


def get_uint64(stream):
    return int.from_bytes(stream.read(8), byteorder='little', signed=False)


def get_uint8(stream):
    return int.from_bytes(stream.read(1), byteorder='little', signed=False)
