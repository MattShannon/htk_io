#!/usr/bin/python
"""A setuptools-based script for distributing and installing htk_io."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.


import os
from setuptools import setup

with open('README.rst') as readmeFile:
    long_description = readmeFile.read()

requires = [ line.rstrip('\n') for line in open('requirements.txt') ]

setup(
    name='htk_io',
    version='0.4',
    description='Read and write HTK and HTS files from python.',
    url='http://github.com/MattShannon/htk_io',
    author='Matt Shannon',
    author_email='matt.shannon@cantab.net',
    license='3-clause BSD (see License file)',
    packages=['htk_io'],
    install_requires=requires,
    scripts=[
        'bin/htk_io_get_label_map_leaf_macro_id_to_leaf_index.py',
        'bin/htk_io_map_alignment_files_label_sublabel_to_leaf_macro_id.py',
        'bin/htk_io_map_alignment_files.py',
    ],
    long_description=long_description,
)
