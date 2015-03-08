"""Tests for functions for reading and writing HTK / HTS alignment files."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import unittest
import doctest
import random
from numpy.random import randint, randn

import htk_io.alignment as alio

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(alio))
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

class SimpleLabelMap(object):
    def __init__(self, ident):
        self.ident = ident

    def __call__(self, label):
        return self.ident, label

def gen_labelMap():
    ident = randint(1000)
    return SimpleLabelMap(ident)

class AlignmentTest(unittest.TestCase):
    def test_SimpleAlignmentIo_writeLines_empty(self):
        framePeriod = gen_framePeriod()
        alignmentIo = alio.SimpleAlignmentIo(framePeriod)
        self.assertEqual(alignmentIo.writeLines([]), [])

    def test_SimpleAlignmentIo_writeLines_single_line(self, its=50):
        for it in range(its):
            framePeriod = gen_framePeriod()
            alignmentIo = alio.SimpleAlignmentIo(framePeriod)
            startTime = randint(-10, 11)
            dur = randint(10)
            endTime = startTime + dur
            label = gen_label()
            alignment = [(startTime, endTime, label, None)]

            alignmentLines = alignmentIo.writeLines(alignment)

            startTicks = int(round(startTime * framePeriod * 1e7))
            endTicks = int(round(endTime * framePeriod * 1e7))
            alignmentLinesGood = ['%s %s %s' % (startTicks, endTicks, label)]
            self.assertEqual(alignmentLines, alignmentLinesGood)

    def test_SimpleAlignmentIo_writeLines_concat(self, its=50):
        for it in range(its):
            framePeriod = gen_framePeriod()
            alignmentIo = alio.SimpleAlignmentIo(framePeriod)
            alignment = gen_alignment()
            breakIndex = randint(len(alignment) + 1)
            alignment0 = alignment[:breakIndex]
            alignment1 = alignment[breakIndex:]

            alignmentLines0 = alignmentIo.writeLines(alignment0)
            alignmentLines1 = alignmentIo.writeLines(alignment1)
            alignmentLines = alignmentIo.writeLines(alignment)
            self.assertEqual(alignmentLines0 + alignmentLines1, alignmentLines)

    def test_SimpleAlignmentIo_readLines(self, its=50):
        for it in range(its):
            alignment = gen_alignment()
            framePeriod = gen_framePeriod()
            alignmentIo = alio.SimpleAlignmentIo(framePeriod)

            alignmentLines = alignmentIo.writeLines(alignment)
            alignmentAgain = alignmentIo.readLines(alignmentLines)
            self.assertEqual(alignmentAgain, alignment)

    def test_flatten_1_level(self, its=50):
        for it in range(its):
            alignment = gen_alignment()

            flatAlignment = alio.flatten(alignment)

            flatAlignmentGood = [
                (startTime, endTime, (label,), None)
                for startTime, endTime, label, subAlignment in alignment
            ]
            self.assertEqual(flatAlignment, flatAlignmentGood)

    def test_flatten_nested(self, its=50):
        for it in range(its):
            numLevels = randint(2, 4)
            alignment = gen_alignment(numLevels=numLevels)

            flatAlignment = alio.flatten(alignment)

            flatAlignmentNested = alio.flatten([
                (startTime, endTime, label, alio.flatten(subAlignment))
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

    def test_unflatten(self, its=50):
        for it in range(its):
            numLevels = randint(1, 4)
            alignment = gen_alignment(numLevels=numLevels)

            flatAlignment = alio.flatten(alignment)
            alignmentAgain = alio.unflatten(flatAlignment)
            self.assertEqual(alignmentAgain, alignment)

    def test_AlignmentIo_writeLines_1_level(self, its=50):
        for it in range(its):
            framePeriod = gen_framePeriod()
            alignment = gen_alignment()
            simpleAlignmentIo = alio.SimpleAlignmentIo(framePeriod)
            alignmentIo = alio.AlignmentIo(framePeriod)

            self.assertEqual(
                simpleAlignmentIo.writeLines(alignment),
                alignmentIo.writeLines(alignment)
            )

    def test_AlignmentIo_writeLines_nested(self, its=50):
        for it in range(its):
            numLevels = randint(2, 4)
            alignment = gen_alignment(numLevels=numLevels)
            framePeriod = gen_framePeriod()
            alignmentIo = alio.AlignmentIo(framePeriod)

            alignmentLines = alignmentIo.writeLines(alignment)

            alignmentLinesAgain = []
            for startTime, endTime, label, subAlignment in alignment:
                subAlignmentLines = alignmentIo.writeLines(subAlignment)
                alignmentLinesAgain.append(subAlignmentLines[0] + ' ' + label)
                alignmentLinesAgain.extend(subAlignmentLines[1:])

            self.assertEqual(alignmentLinesAgain, alignmentLines)

    def test_AlignmentIo_readLines(self, its=50):
        for it in range(its):
            numLevels = randint(1, 4)
            alignment = gen_alignment(numLevels=numLevels)
            framePeriod = gen_framePeriod()
            alignmentIo = alio.AlignmentIo(framePeriod)

            alignmentLines = alignmentIo.writeLines(alignment)
            alignmentAgain = alignmentIo.readLines(alignmentLines)
            self.assertEqual(alignmentAgain, alignment)

    def test_mapAlignmentLabels_1_level(self, its=50):
        for it in range(its):
            alignment = gen_alignment()
            labelMap = gen_labelMap()

            alignmentNew = alio.mapAlignmentLabels(alignment, [labelMap])

            alignmentNewGood = [
                (startTime, endTime, labelMap(label), None)
                for startTime, endTime, label, subAlignment in alignment
            ]
            self.assertEqual(alignmentNew, alignmentNewGood)

    def test_mapAlignmentLabels_nested(self, its=50):
        for it in range(its):
            numLevels = randint(2, 4)
            alignment = gen_alignment(numLevels=numLevels)
            labelMaps = [ gen_labelMap() for _ in range(numLevels) ]

            alignmentNew = alio.mapAlignmentLabels(alignment, labelMaps)

            alignmentNewAgain = [
                (
                    startTime, endTime, labelMaps[0](label),
                    alio.mapAlignmentLabels(subAlignment, labelMaps[1:])
                )
                for startTime, endTime, label, subAlignment in alignment
            ]

            self.assertEqual(alignmentNewAgain, alignmentNew)

if __name__ == '__main__':
    unittest.main()
