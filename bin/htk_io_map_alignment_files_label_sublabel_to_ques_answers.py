#!/usr/bin/python
"""Maps each (label, sublabel) in each alignment file to a vector of answers.

Given an HTK / HTS question file (as used to perform decision tree clustering)
and a collection of two-level (label, sublabel) alignment files, this command
maps each (label, sublabel) pair to the vector of answers to each of the
questions in the question file.
The result is a collection of 1-level alignment files where each label is a
vector of question answers.

Two-level (label, sublabel) alignment files suitable for input to this command
may be obtained using HTS's HSMMAlign command with the -f flag.
"""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import os
import sys
import argparse

import htk_io.alignment as alio
import htk_io.ques as qio

def mapAlignment(alignment, quesRes, subLabelStrEnds):
    numSubLabels = len(subLabelStrEnds)

    alignmentNew = []
    for startTime, endTime, label, subAlignment in alignment:
        assert len(subAlignment) == len(subLabelStrEnds)

        answerVec = [ quesRe.match(label) for quesRe in quesRes ]
        answerVecStr = ','.join(map(lambda x: ('1' if x else '0'), answerVec))

        for subLabelIndex, (subStartTime, subEndTime, subLabelStr, _) in (
            enumerate(subAlignment)
        ):
            assert subLabelStr.endswith(subLabelStrEnds[subLabelIndex])

            alignmentNew.append((
                subStartTime,
                subEndTime,
                '%s,%s' % ((subLabelIndex + 0.5) / numSubLabels, answerVecStr),
                None
            ))

    return alignmentNew

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument(
        '--alignment_suffix', dest='alignmentSuffix',
        metavar='ALIGNSUFFIX',
        default='lab',
        help='suffix for alignment files (e.g. "lab")'
    )
    parser.add_argument(
        '--sublabel_pat', dest='subLabelStrEndPat',
        metavar='PAT',
        default='[%d]',
        help=('printf-style pattern which, when expanded by replacing %%d with'
              ' a sublabel index >= 2, specifies the last part of the sublabel'
              ' string used in the input alignment files'
              ' (e.g. "[%%d]")')
    )
    parser.add_argument(
        '--num_sublabels', dest='numSubLabels', metavar='NUMSUBLABELS',
        default=5, type=int,
        help=('number of sublabels (also sometimes known as "states") in input'
              ' alignments (e.g. "5")')
    )
    parser.add_argument(
        dest='quesFile', metavar='QUESFILE',
        help='HTK / HTS question file (e.g. "questions_qst001.hed")'
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

    subLabelStrEnds = [
        args.subLabelStrEndPat % (subLabelIndex + 2)
        for subLabelIndex in range(args.numSubLabels)
    ]

    alignmentIo = alio.AlignmentIo(framePeriod=1e-7)

    questions = qio.readQuesFileVerifying(args.quesFile)
    quesRes = [ qio.getQuesRe(quesPats) for _, quesPats in questions ]

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
        alignmentNew = mapAlignment(alignment, quesRes, subLabelStrEnds)
        alignmentIo.writeFile(alignmentFileOut, alignmentNew)

if __name__ == '__main__':
    main(sys.argv)
