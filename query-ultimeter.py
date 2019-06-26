#!/usr/bin/env python3

import dataplex
import time

source = dataplex.SourceUltimeter()

while True:
    print(source.collect())
    time.sleep(0.1)
