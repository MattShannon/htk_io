"""Tests for functions for reading and writing HTK / HTS alignment files."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import htk_io.alignment

import unittest
import doctest
import random

from numpy.random import randint, randn

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(htk_io.alignment))
    return tests

def gen_label(size=None, minSize=1, alphabet=None):
    if size is None:
        size = minSize + randint(2)
    if alphabet is None:
        alphabet = ['a', 'b']
    label = ''.join([
        random.choice(alphabet)
        for _ in range(size)
    ])
    return label

def gen_alignment(startTimeInit=None, numLevels=1,
                  size=None, minSize=0, minSizeSub=1, minDur=0,
                  labelMinSize=1, labelAlphabet=None):
    """Returns an alignment."""
    if startTimeInit is None:
        startTimeInit = random.choice([0, randint(-10, 11)])
    assert numLevels >= 1
    if size is None:
        size = minSize + random.choice([randint(3), randint(6)])

    alignment = []
    startTime = startTimeInit
    for _ in range(size):
        label = gen_label(minSize=labelMinSize, alphabet=labelAlphabet)
        if numLevels == 1:
            dur = minDur + random.choice([randint(3), randint(10)])

            endTime = startTime + dur
            subAlignment = None
        else:
            subAlignment = gen_alignment(
                startTimeInit=startTime,
                numLevels=(numLevels - 1),
                size=None,
                minSize=minSizeSub,
                minSizeSub=minSizeSub,
                minDur=minDur,
                labelMinSize=labelMinSize,
                labelAlphabet=labelAlphabet,
            )
            if not subAlignment:
                endTime = startTime
            else:
                endTime = subAlignment[-1][1]

        alignment.append((startTime, endTime, label, subAlignment))
        startTime = endTime

    return alignment

def gen_framePeriod():
    """Returns a frame period.

    Specifically, returns a frame period such that writing-then-reading
    alignments should be lossless.
    """
    while True:
        framePeriod = abs(randn()) * 3e-7
        if framePeriod >= 1e-7:
            break

    return framePeriod

class AlignmentTest(unittest.TestCase):
    def test_writeSimpleAlignmentLines_empty(self):
        framePeriod = gen_framePeriod()
        self.assertEqual(
            htk_io.alignment.writeSimpleAlignmentLines([], framePeriod),
            []
        )

    def test_writeSimpleAlignmentLines_single_line(self, its=50):
        for it in range(its):
            framePeriod = gen_framePeriod()
            startTime = randint(-10, 11)
            dur = randint(10)
            endTime = startTime + dur
            label = gen_label()
            alignment = [(startTime, endTime, label, None)]

            alignmentLines = htk_io.alignment.writeSimpleAlignmentLines(
                alignment, framePeriod
            )

            startTicks = int(round(startTime * framePeriod * 1e7))
            endTicks = int(round(endTime * framePeriod * 1e7))
            alignmentLinesGood = ['%s %s %s' % (startTicks, endTicks, label)]
            self.assertEqual(alignmentLines, alignmentLinesGood)

    def test_writeSimpleAlignmentLines_concat(self, its=50):
        for it in range(its):
            framePeriod = gen_framePeriod()
            alignment = gen_alignment()
            breakIndex = randint(len(alignment) + 1)
            alignment0 = alignment[:breakIndex]
            alignment1 = alignment[breakIndex:]

            alignmentBla0 = htk_io.alignment.writeSimpleAlignmentLines(
                alignment0, framePeriod
            )
            alignmentBla1 = htk_io.alignment.writeSimpleAlignmentLines(
                alignment1, framePeriod
            )
            alignmentBla = htk_io.alignment.writeSimpleAlignmentLines(
                alignment, framePeriod
            )
            self.assertEqual(alignmentBla0 + alignmentBla1, alignmentBla)

    def test_writeSimpleAlignmentLines_readSimpleAlignmentLines(self, its=50):
        for it in range(its):
            alignment = gen_alignment()
            framePeriod = gen_framePeriod()

            alignmentLines = htk_io.alignment.writeSimpleAlignmentLines(
                alignment, framePeriod
            )
            alignmentAgain = htk_io.alignment.readSimpleAlignmentLines(
                alignmentLines, framePeriod
            )
            self.assertEqual(alignmentAgain, alignment)

    def test_flatten_1_level(self, its=50):
        for it in range(its):
            alignment = gen_alignment()

            flatAlignment = htk_io.alignment.flatten(alignment)

            flatAlignmentGood = [
                (startTime, endTime, (label,), None)
                for startTime, endTime, label, subAlignment in alignment
            ]
            self.assertEqual(flatAlignment, flatAlignmentGood)

    def test_flatten_nested(self, its=50):
        for it in range(its):
            numLevels = randint(2, 4)
            alignment = gen_alignment(numLevels=numLevels)

            flatAlignment = htk_io.alignment.flatten(alignment)

            flatAlignmentNested = htk_io.alignment.flatten([
                (
                    startTime, endTime, label,
                    htk_io.alignment.flatten(subAlignment)
                )
                for startTime, endTime, label, subAlignment in alignment
            ])

            def getLabelTuple(labelTupleTuple):
                if len(labelTupleTuple) == 1:
                    labelTuple = labelTupleTuple[0]
                else:
                    labelRest, labelOuter = labelTupleTuple
                    labelTuple = labelRest + (labelOuter,)
                return labelTuple

            flatAlignmentAgain = [
                (
                    startTime, endTime, getLabelTuple(labelTupleTuple),
                    subAlignment
                )
                for startTime, endTime, labelTupleTuple, subAlignment in (
                    flatAlignmentNested
                )
            ]
            self.assertEqual(flatAlignmentAgain, flatAlignment)

    def test_flatten_unflatten(self, its=50):
        for it in range(its):
            numLevels = randint(1, 4)
            alignment = gen_alignment(numLevels=numLevels)

            flatAlignment = htk_io.alignment.flatten(alignment)
            alignmentAgain = htk_io.alignment.unflatten(flatAlignment)
            self.assertEqual(alignmentAgain, alignment)

    def test_writeAlignmentLines_1_level(self, its=50):
        for it in range(its):
            framePeriod = gen_framePeriod()
            alignment = gen_alignment()

            self.assertEqual(
                htk_io.alignment.writeSimpleAlignmentLines(
                    alignment, framePeriod
                ),
                htk_io.alignment.writeAlignmentLines(
                    alignment, framePeriod
                )
            )

    def test_writeAlignmentLines_nested(self, its=50):
        for it in range(its):
            numLevels = randint(2, 4)
            alignment = gen_alignment(numLevels=numLevels)
            framePeriod = gen_framePeriod()

            alignmentLines = htk_io.alignment.writeAlignmentLines(
                alignment, framePeriod
            )

            alignmentLinesAgain = []
            for startTime, endTime, label, subAlignment in alignment:
                subAlignmentLines = htk_io.alignment.writeAlignmentLines(
                    subAlignment, framePeriod
                )
                alignmentLinesAgain.append(subAlignmentLines[0] + ' ' + label)
                alignmentLinesAgain.extend(subAlignmentLines[1:])

            self.assertEqual(alignmentLinesAgain, alignmentLines)

    def test_writeAlignmentLines_readAlignmentLines(self, its=50):
        for it in range(its):
            numLevels = randint(1, 4)
            alignment = gen_alignment(numLevels=numLevels)
            framePeriod = gen_framePeriod()

            alignmentLines = htk_io.alignment.writeAlignmentLines(
                alignment, framePeriod
            )
            alignmentAgain = htk_io.alignment.readAlignmentLines(
                alignmentLines, framePeriod
            )
            self.assertEqual(alignmentAgain, alignment)

if __name__ == '__main__':
    unittest.main()
