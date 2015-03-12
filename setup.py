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
    version='0.4.dev1',
    description='Read and write HTK and HTS files from python.',
    url='http://github.com/MattShannon/htk_io',
    author='Matt Shannon',
    author_email='matt.shannon@cantab.net',
    license='3-clause BSD (see License file)',
    packages=['htk_io'],
    install_requires=requires,
    long_description=long_description,
)
