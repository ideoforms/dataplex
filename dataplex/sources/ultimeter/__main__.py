import time

from .source import SourceUltimeter

if __name__ == "__main__":
    source = SourceUltimeter()

    while True:
        print(source.collect())
        time.sleep(0.1)