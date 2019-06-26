#!/usr/bin/env python3

import dataplex
import time

source = dataplex.SourceAudio()

while True:
    print(source.collect())
    time.sleep(0.1)
