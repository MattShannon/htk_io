"""Tests for common functions and classes for I/O."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import unittest
import doctest

import htk_io.base

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(htk_io.base))
    return tests

# FIXME : add tests
class BaseTest(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
