"""Helper functions for I/O."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import re

def stripQuotes(s):
    assert len(s) >= 2 and s[0] == '"' and s[-1] == '"'

    return s[1:-1]

def addQuotes(s):
    return '"%s"' % s

whitespaceRe = re.compile(r'\s+')
whitespaceEolRe = re.compile(r'\s+$')

def normalizeWhitespace(lines):
    outLines = []
    for line in lines:
        outLine = line
        outLine = re.sub(whitespaceRe, ' ', outLine)
        outLine = re.sub(whitespaceEolRe, '', outLine)
        if outLine != '':
            outLines.append(outLine)
    return outLines

def verifiedRead(read, write, lines, unpack=False):
    data = read(lines)
    if unpack:
        linesOut = write(*data)
    else:
        linesOut = write(data)

    lines = normalizeWhitespace(lines)
    linesOut = normalizeWhitespace(linesOut)

    if linesOut != lines:
        for line, lineOut in zip(lines, linesOut):
            if line != lineOut:
                print line
                print ' !='
                print lineOut
                raise RuntimeError('verified read failed')
        assert len(line) != len(lineOut)
        print 'lengths differ: %s vs %s' % (len(line), len(lineOut))
        raise RuntimeError('verified read failed')

    return data
