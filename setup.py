#!/usr/bin/env python3

from setuptools import setup

setup(
    name = 'dataplex',
    version = '0.0.1',
    description = 'dataplex, a data I/O hub designed for real-time analysis and performance systems',
    long_description = open("README.md", "r").read(),
    long_description_content_type = "text/markdown",
    author = 'Daniel Jones',
    author_email = 'dan-code@erase.net',
    url = 'https://github.com/ideoforms/dataplex',
    packages = ['dataplex'],
    keywords = ('data', 'analysis', 'statistics', 'sound', 'music'),
    install_requires = ["pydantic==2.8.2", "pyserial", "python-osc", "numpy", "pandas", "jdp", "mido", "signalflow", "pyyaml"],
    classifiers = [
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Artistic Software',
        'Topic :: Communications',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ]
)
