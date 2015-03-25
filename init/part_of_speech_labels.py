
from gargantext_web.db import *

# Instantiante table NgramTag:
f = open("part_of_speech_labels.txt", 'r')

for line in f.readlines():
    name, description = line.strip().split('\t')
    _tag = Tag(name=name, description=description)
    session.add(_tag)
session.commit()
f.close()


