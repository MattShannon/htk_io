#!/usr/bin/python
"""Maps each label in each alignment file using a user-specified mapping.

If an input alignment file has multiple levels then only the last (i.e. the
innermost, i.e the fastest-changing) level is considered.
"""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import os
import sys
import argparse

import htk_io.alignment as alio

def readLabelMapFile(labelMapFile):
    labelMapDict = dict()
    for line in open(labelMapFile):
        labelKey, labelValue = line.rstrip('\n').split()
        if labelKey in labelMapDict:
            raise RuntimeError('multiple values given for key %s' % labelKey)
        labelMapDict[labelKey] = labelValue

    return labelMapDict

def mapAlignment(labelMapDict, alignment):
    alignmentNew = []
    for startTime, endTime, label, _ in alignment:
        labelNew = labelMapDict[label]
        alignmentNew.append((startTime, endTime, labelNew, None))

    return alignmentNew

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument(
        '--alignment_suffix', dest='alignmentSuffix',
        metavar='ALIGNSUFFIX',
        default='lab',
        help='suffix for alignment files'
    )
    parser.add_argument(
        dest='labelMapFile', metavar='LABELMAP',
        help=('file specifying label mapping'
              ' (two columns separated by whitespace)')
    )
    parser.add_argument(
        dest='alignmentDirIn', metavar='ALIGNDIRIN',
        help='directory to read input alignments from'
    )
    parser.add_argument(
        dest='uttIdsFile', metavar='UTTIDSFILE',
        help=('file containing a list of utterance ids'
              ' (e.g. one line might be "cmu_us_arctic_slt_a0001")')
    )
    parser.add_argument(
        dest='alignmentDirOut', metavar='ALIGNDIROUT',
        help='directory to write output alignments to'
    )
    args = parser.parse_args(argv[1:])

    uttIds = [ line.strip() for line in open(args.uttIdsFile) ]

    alignmentIo = alio.AlignmentIo(framePeriod=1e-7)

    labelMapDict = readLabelMapFile(args.labelMapFile)
    print '(read label map with %s entries)' % len(labelMapDict)

    print '(writing output to directory %s)' % args.alignmentDirOut
    for uttId in uttIds:
        alignmentFileIn = os.path.join(
            args.alignmentDirIn,
            '%s.%s' % (uttId, args.alignmentSuffix)
        )
        alignmentFileOut = os.path.join(
            args.alignmentDirOut,
            '%s.%s' % (uttId, args.alignmentSuffix)
        )

        alignment = alignmentIo.readFile(alignmentFileIn)
        alignmentNew = mapAlignment(labelMapDict, alignment)
        alignmentIo.writeFile(alignmentFileOut, alignmentNew)

if __name__ == '__main__':
    main(sys.argv)
