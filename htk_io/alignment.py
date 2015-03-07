"""Functions for reading and writing HTK / HTS alignment files.

HTK / HTS alignment files are often referred to as "label" files.

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

class AlignmentIoBase(object):
    """An abstract class for reading and writing HTK-style alignment files."""
    def writeFile(self, filename, alignment):
        lines = self.writeLines(alignment)
        with open(filename, 'w') as f:
            for line in lines:
                f.write(line)
                f.write('\n')

    def readFile(self, filename):
        alignmentLines = [ line.rstrip('\n') for line in open(filename, 'U') ]
        return self.readLines(alignmentLines)

class SimpleAlignmentIo(AlignmentIoBase):
    """Reads and writes 1-level HTK-style alignment files.

    The amount of time between one frame and the next is specified by the float
    `framePeriod` in seconds.

    In most cases it is probably preferable to use `AlignmentIo` instead of
    this class since it supports multilevel alignments.
    """
    def __init__(self, framePeriod):
        self.framePeriod = framePeriod

        if self.framePeriod < 1e-7:
            # N.B. I believe write-then-read is guaranteed to recover original
            #   integer-valued segment timings as long as framePeriod >= 1e-7
            raise RuntimeError(
                'writing alignment files may be lossy since specified'
                ' frame period is extremely small'
            )

    def writeLines(self, alignment):
        """Writes the lines of a 1-level HTK-style alignment file.

        Use `writeFile` method to write an actual file.

        See the 1-level alignment examples in the documentation for
        `AlignmentIo.writeLines` for examples of usage of this method.
        """
        divisor = self.framePeriod * 1e7

        alignmentLines = []
        for startTime, endTime, label, subAlignment in alignment:
            assert subAlignment is None
            startTicks = int(round(startTime * divisor))
            endTicks = int(round(endTime * divisor))
            alignmentLines.append('%s %s %s' % (startTicks, endTicks, label))

        return alignmentLines

    def readLines(self, alignmentLines):
        """Reads the lines of a 1-level HTK-style alignment file.

        Use `readFile` method to read an actual file.

        See the 1-level alignment examples in the documentation for
        `AlignmentIo.readLines` for examples of usage of this method.
        """
        divisor = self.framePeriod * 1e7

        alignment = []
        for line in alignmentLines:
            startTicks, endTicks, label = line.strip().split(None, 2)
            startTime = int(round(int(startTicks) / divisor))
            endTime = int(round(int(endTicks) / divisor))
            alignment.append((startTime, endTime, label, None))

        return alignment

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

class AlignmentIo(AlignmentIoBase):
    """Reads and writes HTK-style alignment files.

    Example usage:

    >>> import htk_io.alignment
    >>> alignmentIo = htk_io.alignment.AlignmentIo(framePeriod=1.0)
    >>> alignmentIo.writeLines([
    ...     (0, 1, 'the', None),
    ...     (1, 2, 'cat', None),
    ...     (2, 5, 'cat', None),
    ...     (5, 6, 'sat', None),
    ... ]) == [
    ...     '0 10000000 the',
    ...     '10000000 20000000 cat',
    ...     '20000000 50000000 cat',
    ...     '50000000 60000000 sat',
    ... ]
    True
    >>> alignmentIo.readLines([
    ...     '0 10000000 the',
    ...     '10000000 20000000 cat',
    ...     '20000000 50000000 cat',
    ...     '50000000 60000000 sat',
    ... ]) == [
    ...     (0, 1, 'the', None),
    ...     (1, 2, 'cat', None),
    ...     (2, 5, 'cat', None),
    ...     (5, 6, 'sat', None),
    ... ]
    True

    The amount of time between one frame and the next is specified by the float
    `framePeriod` in seconds.

    >>> alignmentIo2 = htk_io.alignment.AlignmentIo(framePeriod=0.5)
    >>> alignmentIo2.writeLines([
    ...     (0, 2, 'the', None),
    ...     (2, 4, 'cat', None),
    ...     (4, 10, 'cat', None),
    ...     (10, 12, 'sat', None),
    ... ]) == [
    ...     '0 10000000 the',
    ...     '10000000 20000000 cat',
    ...     '20000000 50000000 cat',
    ...     '50000000 60000000 sat',
    ... ]
    True
    >>> alignmentIo2.readLines([
    ...     '0 10000000 the',
    ...     '10000000 20000000 cat',
    ...     '20000000 50000000 cat',
    ...     '50000000 60000000 sat',
    ... ]) == [
    ...     (0, 2, 'the', None),
    ...     (2, 4, 'cat', None),
    ...     (4, 10, 'cat', None),
    ...     (10, 12, 'sat', None),
    ... ]
    True

    A check is performed to ensure that no information will be lost by the
    conversion from number of frames to units of 1e-7 seconds that happens
    during alignment writing:

    >>> alignmentIo3 = htk_io.alignment.AlignmentIo(framePeriod=5e-8)
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    RuntimeError: writing alignment files may be lossy...

    Alignments not starting at time zero are supported:

    >>> alignmentIo.writeLines([
    ...     (5, 6, 'the', None),
    ...     (6, 8, 'cat', None),
    ... ]) == [
    ...     '50000000 60000000 the',
    ...     '60000000 80000000 cat',
    ... ]
    True
    >>> alignmentIo.readLines([
    ...     '50000000 60000000 the',
    ...     '60000000 80000000 cat',
    ... ]) == [
    ...     (5, 6, 'the', None),
    ...     (6, 8, 'cat', None),
    ... ]
    True
    >>> alignmentIo.writeLines([
    ...     (-6, -5, 'the', None),
    ...     (-5, 4, 'cat', None),
    ... ]) == [
    ...     '-60000000 -50000000 the',
    ...     '-50000000 40000000 cat',
    ... ]
    True
    >>> alignmentIo.readLines([
    ...     '-60000000 -50000000 the',
    ...     '-50000000 40000000 cat',
    ... ]) == [
    ...     (-6, -5, 'the', None),
    ...     (-5, 4, 'cat', None),
    ... ]
    True

    It supports multilevel alignments.
    For example for a 2-level alignment:

    >>> alignmentIo.writeLines([
    ...     (0, 3, 'the', [
    ...         (0, 2, 'X', None),
    ...         (2, 3, 'Y', None),
    ...     ]),
    ...     (3, 6, 'cat', [
    ...         (3, 4, 'Y', None),
    ...         (4, 6, 'X', None),
    ...     ]),
    ... ]) == [
    ...     '0 20000000 X the',
    ...     '20000000 30000000 Y',
    ...     '30000000 40000000 Y cat',
    ...     '40000000 60000000 X',
    ... ]
    True
    >>> alignmentIo.readLines([
    ...     '0 20000000 X the',
    ...     '20000000 30000000 Y',
    ...     '30000000 40000000 Y cat',
    ...     '40000000 60000000 X',
    ... ]) == [
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

    >>> alignmentIo.writeLines([
    ...     (0, 360000, 'a', None),
    ... ]) == [
    ...     '0 3600000000000 a',
    ... ]
    True
    >>> alignmentIo.readLines([
    ...     '0 3600000000000 a',
    ... ]) == [
    ...     (0, 360000, 'a', None),
    ... ]
    True
    >>> alignmentIo.writeLines([
    ...     (-360000, 0, 'a', None),
    ... ]) == [
    ...     '-3600000000000 0 a',
    ... ]
    True
    >>> alignmentIo.readLines([
    ...     '-3600000000000 0 a',
    ... ]) == [
    ...     (-360000, 0, 'a', None),
    ... ]
    True
    """
    def __init__(self, framePeriod, levelSep=None):
        self.framePeriod = framePeriod
        self.levelSep = levelSep

        self.simpleIo = SimpleAlignmentIo(self.framePeriod)

    def writeLines(self, alignment):
        """Writes the lines of an HTK-style alignment file.

        Use `writeFile` method to write an actual file.
        """
        levelSep = ' ' if self.levelSep is None else self.levelSep

        flatAlignment = flatten(alignment)
        rawAlignment = [
            (startTime, endTime, levelSep.join(labelTuple), subAlignment)
            for startTime, endTime, labelTuple, subAlignment in flatAlignment
        ]
        alignmentLines = self.simpleIo.writeLines(rawAlignment)
        return alignmentLines

    def readLines(self, alignmentLines):
        """Reads the lines of an HTK-style alignment file.

        Use `readFile` method to read an actual file.
        """
        rawAlignment = self.simpleIo.readLines(alignmentLines)
        flatAlignment = [
            (startTime, endTime, label.split(self.levelSep), subAlignment)
            for startTime, endTime, label, subAlignment in rawAlignment
        ]
        alignment = unflatten(flatAlignment)
        return alignment

def mapAlignmentLabels(alignment, labelMaps):
    """Transforms an alignment by mapping the labels at each depth.

    Labels at the highest level are mapped using labelMaps[0], and labels at
    the second highest level are mapped using labelMaps[1], etc.
    """
    if not labelMaps:
        return alignment
    else:
        labelMap = labelMaps[0]
        subLabelMaps = labelMaps[1:]
        return [
            (
                startTime,
                endTime,
                labelMap(label),
                mapAlignmentLabels(subAlignment, subLabelMaps)
            )
            for startTime, endTime, label, subAlignment in alignment
        ]

class AlignmentLabelTransform(object):
    """Transforms an alignment by mapping the labels at each depth.

    Labels at the highest level are mapped using labelMaps[0], and labels at
    the second highest level are mapped using labelMaps[1], etc.

    Example usage:

    >>> import htk_io.alignment
    >>> alignmentLabelTransform = htk_io.alignment.AlignmentLabelTransform(
    ...     [lambda label: label == 'cat']
    ... )
    >>> alignmentLabelTransform([
    ...     (0, 1, 'the', None),
    ...     (1, 2, 'cat', None),
    ...     (2, 5, 'cat', None),
    ...     (5, 6, 'sat', None),
    ... ]) == [
    ...     (0, 1, False, None),
    ...     (1, 2, True, None),
    ...     (2, 5, True, None),
    ...     (5, 6, False, None),
    ... ]
    True

    If each of the label transforms has an `inv` method to compute the inverse
    then so does the overall alignment transform:

    >>> class SimpleTransform(object):
    ...     def __call__(self, string):
    ...         return list(string)
    ...
    ...     def inv(self, _list):
    ...         return ''.join(_list)
    ...
    >>> alignmentLabelTransform = htk_io.alignment.AlignmentLabelTransform(
    ...     [SimpleTransform()]
    ... )
    >>> alignmentLabelTransform([
    ...     (0, 1, 'the', None),
    ...     (1, 2, 'cat', None),
    ...     (2, 5, 'cat', None),
    ...     (5, 6, 'sat', None),
    ... ]) == [
    ...     (0, 1, ['t', 'h', 'e'], None),
    ...     (1, 2, ['c', 'a', 't'], None),
    ...     (2, 5, ['c', 'a', 't'], None),
    ...     (5, 6, ['s', 'a', 't'], None),
    ... ]
    True
    >>> alignmentLabelTransform.inv([
    ...     (0, 1, ['t', 'h', 'e'], None),
    ...     (1, 2, ['c', 'a', 't'], None),
    ...     (2, 5, ['c', 'a', 't'], None),
    ...     (5, 6, ['s', 'a', 't'], None),
    ... ]) == [
    ...     (0, 1, 'the', None),
    ...     (1, 2, 'cat', None),
    ...     (2, 5, 'cat', None),
    ...     (5, 6, 'sat', None),
    ... ]
    True
    """
    def __init__(self, labelTransforms):
        self.labelTransforms = labelTransforms

        try:
            self.labelTransformInvs = [
                labelTransform.inv
                for labelTransform in self.labelTransforms
            ]
        except:
            pass

    def __call__(self, alignment):
        return mapAlignmentLabels(alignment, self.labelTransforms)

    def inv(self, alignmentNew):
        return mapAlignmentLabels(alignmentNew, self.labelTransformInvs)

class AlignmentGetter(object):
    """This class reads alignment files on demand from a directory.

    Example usage (assumes the current directory contains the "example"
    subdirectory included in source code for this package):

    >>> import htk_io.alignment
    >>> alignmentIo = htk_io.alignment.AlignmentIo(framePeriod=0.005)
    >>> alignmentGetter = htk_io.alignment.AlignmentGetter(
    ...     alignmentIo, alignmentDir='example'
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

    >>> alignmentIo2 = htk_io.alignment.AlignmentIo(framePeriod=1.0)
    >>> alignmentGetter2 = htk_io.alignment.AlignmentGetter(
    ...     alignmentIo2, alignmentDir='example'
    ... )
    >>> alignmentGetter2('example-3-level') == [
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
    def __init__(self, alignmentIo, alignmentDir, alignmentExt='lab',
                 transform=None):
        self.alignmentIo = alignmentIo
        self.alignmentDir = alignmentDir
        self.alignmentExt = alignmentExt
        self.transform = transform

    def __call__(self, uttId):
        alignmentFile = os.path.join(
            self.alignmentDir,
            '%s.%s' % (uttId, self.alignmentExt)
        )
        alignment = self.alignmentIo.readFile(alignmentFile)
        if self.transform is not None:
            alignment = self.transform(alignment)
        return alignment
