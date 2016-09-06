"""
Creates MD5 hashes (used for unique filepaths)
NB this module could go inside util.files
"""

import hashlib
import binascii


def digest(value, algorithm='md5'):
    """
    Ex: b'm\x00\x07\xe5/z\xfb}Z\x06P\xb0\xff\xb8\xa4\xd1'

    (16 bytes ranging from 0 to ff)
    """
    m = hashlib.new(algorithm)
    m.update(value)
    return m.digest()

def str_digest(value, algorithm='md5'):
    """
    Ex: 6d0007e52f7afb7d5a0650b0ffb8a4d1

    (32 hex chars)
    """
    return binascii.hexlify(digest(value, algorithm)).decode()
