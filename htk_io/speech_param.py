"""Functions for reading and writing HTS speech parameter files.

A speech parameter file consists of a sequence of speech parameter vectors, one
for each frame.
"""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import numpy as np

# FIXME : add tests

def readParamFile(paramFile, paramOrder):
    """Reads an HTS speech parameter file (single precision)."""
    return np.reshape(
        np.fromfile(paramFile, dtype=np.float32),
        (-1, paramOrder)
    ).astype(np.float64)

def readParamFileDouble(paramFile, paramOrder):
    """Reads an HTS speech parameter file (double precision)."""
    return np.reshape(
        np.fromfile(paramFile, dtype=np.float64),
        (-1, paramOrder)
    )

def writeParamFile(outSeq, paramFile):
    """Writes an HTS speech parameter file (single precision)."""
    outSeq.astype(np.float32).tofile(paramFile)

def writeParamFileDouble(outSeq, paramFile):
    """Writes an HTS speech parameter file (double precision)."""
    outSeq.astype(np.float64).tofile(paramFile)
