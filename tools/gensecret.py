#!/usr/bin/env python

from string import ascii_letters as L, digits as D, punctuation as P
from random import SystemRandom as R, randint


def gensecret(chars, min_len=20, max_len=None):
    bounds = (min_len,) if max_len is None else (min_len, max_len)
    return ''.join([R().choice(chars) for i in range(randint(*bounds))])


if __name__ == "__main__":
    import sys

    charsets = {'L': L, 'D': D, 'P': P}
    chars = L+D+P
    bounds = []

    for arg in sys.argv:
        if arg.isalpha():
            chars = ''.join(charsets.get(c, "") for c in arg)
        elif arg.isdigit() and len(bounds) < 2:
            bounds.append(int(arg))

    if not bounds:
        bounds = [45, 50]

    print(gensecret(chars, *bounds))
