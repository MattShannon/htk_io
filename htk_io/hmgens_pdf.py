"""Functions for reading HMGenS-style "pdf" files.

When the HMGenS tool in HTS is run with the '-p' flag, it produces a
probability density function (pdf) file for each utterance and stream.
An HMGenS pdf file specifies Gaussian parameters for each frame, window and
parameter index.
The Gaussian parameters are the b-value (also known as mean-times-precision)
and the precision (also known as inverse variance).

Note that the above interpretation of the values in a HMGenS pdf file as the
b-value and precision of a Gaussian distribution is only valid for the
"standard" model used while training a statistical parametric speech synthesis
system.
This model is not actually a proper probabilistic model of speech parameter
sequences since it models the speech parameter trajectory for each window
separately.
For proper probabilistic models such as the trajectory HMM, the values in an
HMGenS pdf file can be interpreted in a related but different way.
"""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import numpy as np

# FIXME : add tests

# FIXME : change to a HMGenSPdfIo class
def readHMGenSPdf(pdfFile, paramOrder, numWindows):
    """Reads an HMGenS probability density (pdf) file into a numpy array.

    Returns two arrays, each of shape (numTimes, numWindows, paramOrder), the
    first specifying the b-value and the second specifying the precision.
    """
    pdfAll = np.reshape(
        np.fromfile(pdfFile, dtype=np.float32),
        (-1, 2, numWindows, paramOrder)
    ).astype(np.float)
    bWinAll = pdfAll[:, 0]
    tauWinAll = pdfAll[:, 1]
    return bWinAll, tauWinAll
