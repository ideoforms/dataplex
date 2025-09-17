import time
from .source import SourcePakbus

if __name__ == "__main__":
	source = SourcePakbus()
	while True:
		print(source.collect())
		time.sleep(1)
