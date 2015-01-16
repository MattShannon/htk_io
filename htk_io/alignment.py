"""Functions for reading and writing HTK / HTS alignment files.

HTK / HTS alignment files are often also referred to as "label" files.

In this module an alignment is a sequence of segments, where each segment is a
tuple

    (startTime, endTime, label, subAlignment)

where `startTime` and `endTime` are the integer-valued numbers of frames,
`label` is an arbitrary label associated with the segment and `subAlignment` is
an alignment or None (to specify no sub-alignment).
"""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import os

from htk_io.misc import readWrap, writeWrap

def writeSimpleAlignmentLines(alignment, framePeriod):
    """Writes (the lines of) a 1-level HTK-style alignment file.

    Use `writeSimpleAlignmentFile` to write an actual file.

    The amount of time between one frame and the next is specified by the float
    `framePeriod` in seconds.

    In most cases it is probably preferable to use `writeAlignmentLines`
    instead of this function since it supports multilevel alignments.
    See the 1-level alignment examples in the documentation for
    `writeAlignmentLines` for examples of usage of this function.
    """
    if framePeriod < 1e-7:
        # N.B. I believe write-then-read is guaranteed to recover original
        #   integer-valued segment timings as long as framePeriod >= 1e-7
        raise RuntimeError(
            'writing alignment may be lossy since specified frame period is'
            ' extremely small'
        )

    divisor = framePeriod * 1e7

    alignmentLines = []
    for startTime, endTime, label, subAlignment in alignment:
        assert subAlignment is None
        startTicks = int(round(startTime * divisor))
        endTicks = int(round(endTime * divisor))
        alignmentLines.append('%s %s %s' % (startTicks, endTicks, label))

    return alignmentLines

def readSimpleAlignmentLines(alignmentLines, framePeriod):
    """Reads (the lines of) a 1-level HTK-style alignment file.

    Use `readSimpleAlignmentFile` to read an actual file.

    The amount of time between one frame and the next is specified by the float
    `framePeriod` in seconds.

    In most cases it is probably preferable to use `readAlignmentLines` instead
    of this function since it supports multilevel alignments.
    See the 1-level alignment examples in the documentation for
    `readAlignmentLines` for examples of usage of this function.
    """
    divisor = framePeriod * 1e7

    alignment = []
    for line in alignmentLines:
        startTicks, endTicks, label = line.strip().split(None, 2)
        startTime = int(round(int(startTicks) / divisor))
        endTime = int(round(int(endTicks) / divisor))
        alignment.append((startTime, endTime, label, None))

    return alignment

writeSimpleAlignmentFile = writeWrap(writeSimpleAlignmentLines)
readSimpleAlignmentFile = readWrap(readSimpleAlignmentLines)

def flatten(alignment, checkRecover=True):
    """Converts a hierarchical alignment to a flat alignment.

    The flat alignment is a 1-level alignment where each label is a tuple.
    Each element of the tuple corresponds to a different level of the
    hierarchical alignment, with the 0th element of the tuple corresponding to
    the innermost (i.e. the most frequently changing) level of the hierarchical
    alignment.

    For example for a 2-level alignment:

    >>> import htk_io.alignment
    >>> htk_io.alignment.flatten([
    ...     (0, 2, 'a', [
    ...         (0, 1, 'X', None),
    ...         (1, 2, 'Y', None),
    ...     ]),
    ...     (2, 3, 'b', [
    ...         (2, 3, 'Z', None),
    ...     ]),
    ... ]) == [
    ...     (0, 1, ('X', 'a'), None),
    ...     (1, 2, ('Y',), None),
    ...     (2, 3, ('Z', 'b'), None),
    ... ]
    True

    Any sub-alignments should either be non-empty lists or None:

    >>> htk_io.alignment.flatten([
    ...     (0, 1, 'a', []),
    ... ])
    Traceback (most recent call last):
        ...
    RuntimeError: sub-alignment was neither a non-empty list nor None: []
    >>> htk_io.alignment.flatten([
    ...     (0, 1, 'a', [
    ...         (0, 1, 'A', []),
    ...     ]),
    ... ])
    Traceback (most recent call last):
        ...
    RuntimeError: sub-alignment was neither a non-empty list nor None: []

    However for convenience the main alignment is allowed to be an empty list:
    >>> htk_io.alignment.flatten([])
    []

    The hierarchical alignment should be of a consistent depth.
    If `checkRecover` is True then a check is performed to verify that the
    original hierarchical alignment is recoverable from the flat alignment.
    This is the case whenever the restrictions mentioned above are adhered to.

    >>> htk_io.alignment.flatten([
    ...     (0, 2, 'a', [
    ...         (0, 1, 'A', None),
    ...         (1, 2, 'B', None),
    ...     ]),
    ...     (2, 3, 'b', None),
    ... ]) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    RuntimeError: alignment could not be recovered...
    """
    flatAlignment = []
    for startTime, endTime, label, subAlignment in alignment:
        if not subAlignment:
            if subAlignment is not None:
                raise RuntimeError(
                    'sub-alignment was neither a non-empty list nor None: %s' %
                    subAlignment
                )
            flatAlignmentSub = [(startTime, endTime, (), subAlignment)]
        else:
            flatAlignmentSub = flatten(
                subAlignment,
                checkRecover=False
            )
        assert flatAlignmentSub
        for (
            entryIndex, (startTimeSub, endTimeSub, labelTuple, subAlignmentSub)
        ) in enumerate(flatAlignmentSub):
            flatAlignment.append((
                startTimeSub,
                endTimeSub,
                labelTuple if entryIndex > 0 else labelTuple + (label,),
                subAlignmentSub
            ))

    if checkRecover:
        if unflatten(flatAlignment) != alignment:
            raise RuntimeError(
                'alignment could not be recovered from flattened alignment'
                ' (check alignment has consistent depth)'
            )

    return flatAlignment

def unflatten(flatAlignment):
    """Converts a flat alignment to a hierarchical alignment.

    This function is the inverse of `flatten`.

    For example for a 2-level alignment:

    >>> import htk_io.alignment
    >>> htk_io.alignment.unflatten([
    ...     (0, 1, ('X', 'a'), None),
    ...     (1, 2, ('Y',), None),
    ...     (2, 3, ('Z', 'b'), None),
    ... ]) == [
    ...     (0, 2, 'a', [
    ...         (0, 1, 'X', None),
    ...         (1, 2, 'Y', None),
    ...     ]),
    ...     (2, 3, 'b', [
    ...         (2, 3, 'Z', None),
    ...     ]),
    ... ]
    True
    """
    if not flatAlignment:
        assert flatAlignment is not None
        alignment = []
    else:
        numLevels = len(flatAlignment[0][2])
        assert numLevels >= 1

        currLabels = [ None for _ in range(numLevels) ]
        currSubAlignments = [ [] for _ in range(numLevels) ]
        for entry, entryNext in zip(flatAlignment, flatAlignment[1:] + [None]):
            currNumLevels = len(entry[2])
            assert 1 <= currNumLevels <= numLevels

            startTime, endTime, labelTuple, subAlignment = entry
            assert subAlignment is None

            currLabels[:currNumLevels] = labelTuple

            numFreeze = numLevels if entryNext is None else len(entryNext[2])
            for freezeIndex in range(numFreeze):
                label = currLabels[freezeIndex]
                if freezeIndex >= 1:
                    subAlignmentSeg = currSubAlignments[freezeIndex - 1]
                    startTimeSeg = subAlignmentSeg[0][0]
                    endTimeSeg = subAlignmentSeg[-1][1]
                    currSubAlignments[freezeIndex].append(
                        (startTimeSeg, endTimeSeg, label, subAlignmentSeg)
                    )
                    currLabels[freezeIndex] = None
                    currSubAlignments[freezeIndex - 1] = []
                else:
                    currSubAlignments[freezeIndex].append(
                        (startTime, endTime, label, None)
                    )
                    currLabels[freezeIndex] = None

        alignment = currSubAlignments[numLevels - 1]

    return alignment

def writeAlignmentLines(alignment, framePeriod, levelSep=None):
    """Writes (the lines of) an HTK-style alignment file.

    Use `writeAlignmentFile` to write an actual file.

    Example usage:

    >>> import htk_io.alignment
    >>> htk_io.alignment.writeAlignmentLines([
    ...     (0, 1, 'the', None),
    ...     (1, 2, 'cat', None),
    ...     (2, 5, 'cat', None),
    ...     (5, 6, 'sat', None),
    ... ], framePeriod=1.0) == [
    ...     '0 10000000 the',
    ...     '10000000 20000000 cat',
    ...     '20000000 50000000 cat',
    ...     '50000000 60000000 sat',
    ... ]
    True

    The amount of time between one frame and the next is specified by the float
    `framePeriod` in seconds.

    >>> htk_io.alignment.writeAlignmentLines([
    ...     (0, 2, 'the', None),
    ...     (2, 4, 'cat', None),
    ...     (4, 10, 'cat', None),
    ...     (10, 12, 'sat', None),
    ... ], framePeriod=0.5) == [
    ...     '0 10000000 the',
    ...     '10000000 20000000 cat',
    ...     '20000000 50000000 cat',
    ...     '50000000 60000000 sat',
    ... ]
    True

    A check is performed to ensure that no information will be lost by the
    conversion from number of frames to units of 1e-7 seconds that happens
    during alignment writing:

    >>> htk_io.alignment.writeAlignmentLines([
    ...     (0, 1, 'a', None),
    ... ], framePeriod=5e-8) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    RuntimeError: writing alignment may be lossy...

    Alignments not starting at time zero are supported:

    >>> htk_io.alignment.writeAlignmentLines([
    ...     (5, 6, 'the', None),
    ...     (6, 8, 'cat', None),
    ... ], framePeriod=1.0) == [
    ...     '50000000 60000000 the',
    ...     '60000000 80000000 cat',
    ... ]
    True
    >>> htk_io.alignment.writeAlignmentLines([
    ...     (-6, -5, 'the', None),
    ...     (-5, 4, 'cat', None),
    ... ], framePeriod=1.0) == [
    ...     '-60000000 -50000000 the',
    ...     '-50000000 40000000 cat',
    ... ]
    True

    It supports multilevel alignments.
    For example for a 2-level alignment:

    >>> htk_io.alignment.writeAlignmentLines([
    ...     (0, 3, 'the', [
    ...         (0, 2, 'X', None),
    ...         (2, 3, 'Y', None),
    ...     ]),
    ...     (3, 6, 'cat', [
    ...         (3, 4, 'Y', None),
    ...         (4, 6, 'X', None),
    ...     ]),
    ... ], framePeriod=1.0) == [
    ...     '0 20000000 X the',
    ...     '20000000 30000000 Y',
    ...     '30000000 40000000 Y cat',
    ...     '40000000 60000000 X',
    ... ]
    True

    It works even for long utterances:

    >>> htk_io.alignment.writeAlignmentLines([
    ...     (0, 360000, 'a', None),
    ... ], framePeriod=1.0) == [
    ...     '0 3600000000000 a',
    ... ]
    True
    >>> htk_io.alignment.writeAlignmentLines([
    ...     (-360000, 0, 'a', None),
    ... ], framePeriod=1.0) == [
    ...     '-3600000000000 0 a',
    ... ]
    True
    """
    if levelSep is None:
        levelSep = ' '

    flatAlignment = flatten(alignment)
    rawAlignment = [
        (startTime, endTime, levelSep.join(labelTuple), subAlignment)
        for startTime, endTime, labelTuple, subAlignment in flatAlignment
    ]
    alignmentLines = writeSimpleAlignmentLines(rawAlignment, framePeriod)
    return alignmentLines

def readAlignmentLines(alignmentLines, framePeriod, levelSep=None):
    """Reads (the lines of) an HTK-style alignment file.

    Use `readAlignmentFile` to read an actual file.

    Example usage:

    >>> import htk_io.alignment
    >>> htk_io.alignment.readAlignmentLines([
    ...     '0 10000000 the',
    ...     '10000000 20000000 cat',
    ...     '20000000 50000000 cat',
    ...     '50000000 60000000 sat',
    ... ], framePeriod=1.0) == [
    ...     (0, 1, 'the', None),
    ...     (1, 2, 'cat', None),
    ...     (2, 5, 'cat', None),
    ...     (5, 6, 'sat', None),
    ... ]
    True

    The amount of time between one frame and the next is specified by the float
    `framePeriod` in seconds.

    >>> htk_io.alignment.readAlignmentLines([
    ...     '0 10000000 the',
    ...     '10000000 20000000 cat',
    ...     '20000000 50000000 cat',
    ...     '50000000 60000000 sat',
    ... ], framePeriod=0.5) == [
    ...     (0, 2, 'the', None),
    ...     (2, 4, 'cat', None),
    ...     (4, 10, 'cat', None),
    ...     (10, 12, 'sat', None),
    ... ]
    True

    Alignments not starting at time zero are supported:

    >>> htk_io.alignment.readAlignmentLines([
    ...     '50000000 60000000 the',
    ...     '60000000 80000000 cat',
    ... ], framePeriod=1.0) == [
    ...     (5, 6, 'the', None),
    ...     (6, 8, 'cat', None),
    ... ]
    True
    >>> htk_io.alignment.readAlignmentLines([
    ...     '-60000000 -50000000 the',
    ...     '-50000000 40000000 cat',
    ... ], framePeriod=1.0) == [
    ...     (-6, -5, 'the', None),
    ...     (-5, 4, 'cat', None),
    ... ]
    True

    It supports multilevel alignments.
    For example for a 2-level alignments:

    >>> htk_io.alignment.readAlignmentLines([
    ...     '0 20000000 X the',
    ...     '20000000 30000000 Y',
    ...     '30000000 40000000 Y cat',
    ...     '40000000 60000000 X',
    ... ], framePeriod=1.0) == [
    ...     (0, 3, 'the', [
    ...         (0, 2, 'X', None),
    ...         (2, 3, 'Y', None),
    ...     ]),
    ...     (3, 6, 'cat', [
    ...         (3, 4, 'Y', None),
    ...         (4, 6, 'X', None),
    ...     ]),
    ... ]
    True

    It works even for long utterances:

    >>> htk_io.alignment.readAlignmentLines([
    ...     '0 3600000000000 a',
    ... ], framePeriod=1.0) == [
    ...     (0, 360000, 'a', None),
    ... ]
    True
    >>> htk_io.alignment.readAlignmentLines([
    ...     '-3600000000000 0 a',
    ... ], framePeriod=1.0) == [
    ...     (-360000, 0, 'a', None),
    ... ]
    True
    """
    rawAlignment = readSimpleAlignmentLines(alignmentLines, framePeriod)
    flatAlignment = [
        (startTime, endTime, label.split(levelSep), subAlignment)
        for startTime, endTime, label, subAlignment in rawAlignment
    ]
    alignment = unflatten(flatAlignment)
    return alignment

writeAlignmentFile = writeWrap(writeAlignmentLines)
readAlignmentFile = readWrap(readAlignmentLines)

class AlignmentGetter(object):
    """This class reads alignment files on demand from a directory.

    Example usage (assumes the current directory contains the "example"
    subdirectory included in source code for this package):

    >>> import htk_io.alignment
    >>> alignmentGetter = htk_io.alignment.AlignmentGetter(
    ...     framePeriod=0.005, alignmentDir='example'
    ... )
    >>> alignmentGetter('simple') == [
    ...     (0, 10, 'apple', None),
    ...     (10, 41, 'pears', None),
    ... ]
    True

    For a 2-level alignment:

    >>> alignmentGetter('simple-2-level') == [
    ...     (0, 10, 'apple', [
    ...         (0, 2, 'a', None),
    ...         (2, 3, 'p', None),
    ...         (3, 5, 'p', None),
    ...         (5, 8, 'l', None),
    ...         (8, 10, 'e', None),
    ...     ]),
    ...     (10, 41, 'pears', [
    ...         (10, 11, 'p', None),
    ...         (11, 13, 'e', None),
    ...         (13, 14, 'a', None),
    ...         (14, 27, 'r', None),
    ...         (27, 41, 's', None),
    ...     ]),
    ... ]
    True

    Or even a 3-level alignment:

    >>> htk_io.alignment.AlignmentGetter(
    ...     framePeriod=1.0, alignmentDir='example'
    ... )('example-3-level') == [
    ...     (0, 8, '0', [
    ...         (0, 3, 'a', [
    ...             (0, 1, 'A', None),
    ...             (1, 2, 'B', None),
    ...             (2, 3, 'C', None),
    ...         ]),
    ...         (3, 5, 'b', [
    ...             (3, 4, 'D', None),
    ...             (4, 5, 'E', None),
    ...         ]),
    ...         (5, 6, 'c', [
    ...             (5, 6, 'F', None),
    ...         ]),
    ...         (6, 8, 'c', [
    ...             (6, 7, 'G', None),
    ...             (7, 8, 'H', None),
    ...         ]),
    ...     ]),
    ...     (8, 10, '1', [
    ...         (8, 10, 'd', [
    ...             (8, 10, 'I', None),
    ...         ]),
    ...     ]),
    ... ]
    True
    """
    def __init__(self, framePeriod, alignmentDir, alignmentExt='lab',
                 transform=None):
        self.framePeriod = framePeriod
        self.alignmentDir = alignmentDir
        self.alignmentExt = alignmentExt
        self.transform = transform

    def __call__(self, uttId):
        alignmentFile = os.path.join(
            self.alignmentDir,
            '%s.%s' % (uttId, self.alignmentExt)
        )
        alignment = readAlignmentFile(alignmentFile, self.framePeriod)
        if self.transform is not None:
            alignment = self.transform(alignment)
        return alignment
