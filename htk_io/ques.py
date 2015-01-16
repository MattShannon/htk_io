"""Functions for reading and writing HTK / HTS question files."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import re
import fnmatch

from htk_io.misc import stripQuotes, addQuotes, verifiedRead

def getQuesRe(quesPats):
    """Converts a list of question patterns to a regular expression."""
    # N.B. -7 is to get rid of superfluous '\Z(?ms)' at end of string
    quesReStrs = [ fnmatch.translate(quesPat)[:-7] for quesPat in quesPats ]
    quesRe = re.compile(('|'.join(quesReStrs))+'$')
    return quesRe

def getQuesReDict(questions):
    """Returns a dictionary mapping a question id to a regular expression."""
    quesReDict = dict()
    for quesId, quesPats in questions:
        assert quesId not in quesReDict
        quesReDict[quesId] = getQuesRe(quesPats)

    return quesReDict

def parseQuestionLines(lines, isTreeFile=False):
    questions = []
    restIndex = len(lines)
    for lineIndex, line in enumerate(lines):
        line = line.strip()
        fields = line.split()
        if len(fields) > 0:
            if fields[0] == 'QS':
                if isTreeFile:
                    assert len(fields) == 5
                    assert fields[2] == '{'
                    assert fields[4] == '}'
                    quesId = fields[1]
                    quesPats = map(stripQuotes, fields[3].split(','))
                    questions.append((quesId, quesPats))
                else:
                    assert len(fields) == 3
                    assert fields[2][0] == '{'
                    assert fields[2][-1] == '}'
                    quesId = stripQuotes(fields[1])
                    quesPats = fields[2][1:-1].split(',')
                    questions.append((quesId, quesPats))
            else:
                restIndex = lineIndex
                break

    return questions, lines[restIndex:]

def readQuestionLines(lines, isTreeFile=False):
    questions, linesRest = parseQuestionLines(lines, isTreeFile=isTreeFile)
    assert not linesRest
    return questions

def writeQuestionLines(questions, isTreeFile=False):
    outLines = []
    for quesId, quesPats in questions:
        if isTreeFile:
            quesPatsStr = ','.join(map(addQuotes, quesPats))
            outLines.append('QS %s { %s }' % (quesId, quesPatsStr))
        else:
            quesPatsStr = ','.join(quesPats)
            outLines.append('QS %s {%s}' % (addQuotes(quesId), quesPatsStr))

    return outLines

def readQuesFile(quesFile):
    """Reads a question file."""
    lines = [ line.rstrip('\n') for line in open(quesFile, 'U') ]
    questions = readQuestionLines(lines)
    return questions

def readQuesFileVerifying(quesFile):
    """Reads a question file and verifies that it was read correctly.

    Verifies that reconstructing the question file from the parsed output
    reproduces the original question file up to certain whitespace
    substitutions.
    """
    lines = [ line.rstrip('\n') for line in open(quesFile, 'U') ]
    questions = verifiedRead(readQuestionLines, writeQuestionLines, lines)
    return questions

def writeQuesFile(questions, quesFile):
    """Writes a question file."""
    lines = writeQuestionLines(questions)
    with open(quesFile, 'w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')
