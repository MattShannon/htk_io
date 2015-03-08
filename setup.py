#!/usr/bin/python
"""A distutils-based script for distributing and installing htk_io."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.


import os
from distutils.core import setup

with open('README.rst') as readmeFile:
    long_description = readmeFile.read()

setup(
    name='htk_io',
    version='0.2',
    description='Read and write HTK and HTS files from python.',
    url='http://github.com/MattShannon/htk_io',
    author='Matt Shannon',
    author_email='matt.shannon@cantab.net',
    license='3-clause BSD (see License file)',
    packages=['htk_io'],
    long_description=long_description,
)
