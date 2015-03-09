"""Functions for reading and writing raw vector sequence files."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import numpy as np

# FIXME : add tests

class VecSeqIo(object):
    """Reads and writes raw vector sequence files.

    This raw format is used by HTS for speech parameter files (as well as by
    the Speech Processing Toolkit (SPTK) for lots of purposes).
    """
    def __init__(self, vecSize, dtypeFile=np.float32):
        self.vecSize = vecSize
        self.dtypeFile = dtypeFile

    def readFile(self, vecSeqFile):
        """Reads a raw vector sequence file.

        The dtype of the returned numpy array is always the numpy default
        np.float, which may be 32-bit or 64-bit depending on architecture, etc.
        """
        return np.reshape(
            np.fromfile(vecSeqFile, dtype=self.dtypeFile),
            (-1, self.vecSize)
        ).astype(np.float)

    def writeFile(self, vecSeqFile, vecSeq):
        """Writes a raw vector sequence file."""
        vecSeq.astype(self.dtypeFile).tofile(vecSeqFile)

class VecSeqToTraj(object):
    """Extracts one particular trajectory from a vector sequence."""
    def __init__(self, vecIndex):
        self.vecIndex = vecIndex

    def __call__(self, vecSeq):
        # (copy here allows larger array to be garbage collected)
        return vecSeq[:, self.vecIndex].copy()
