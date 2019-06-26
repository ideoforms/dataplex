#!/usr/bin/env python3

import dataplex
import time

source = dataplex.SourceCSV("logs/weather-data.ben-lomond.2015-09-30.131839.csv")

while True:
    print(source.collect())
    time.sleep(0.1)
