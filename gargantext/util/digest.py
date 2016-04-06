import hashlib
import binascii


def digest(value, algorithm='md5'):
    m = hashlib.new(algorithm)
    m.update(value)
    return m.digest()

def str_digest(value, algorithm='md5'):
    return binascii.hexlify(digest(value, algorithm)).decode()
