"""Functions for reading and writing HTK / HTS decision tree files."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

from collections import deque

from htk_io.misc import stripQuotes, addQuotes, verifiedRead
import htk_io.ques as qio

class Leaf(object):
    def __init__(self, macroId):
        self.macroId = macroId

    def __str__(self):
        return addQuotes(self.macroId)

    def __repr__(self):
        return 'Leaf(%r)' % self.macroId

class Tree(object):
    def __init__(self, splitInfos, rootNode):
        self.getQuesId = dict()
        self.getChildren = dict()
        self.splitIdsInOrigOrder = [
            splitId
            for splitId, quesId, leftChild, rightChild in splitInfos
        ]
        for splitId, quesId, leftChild, rightChild in splitInfos:
            self.getQuesId[splitId] = quesId
            self.getChildren[splitId] = [leftChild, rightChild]

        self.rootNode = rootNode
        assert (isinstance(self.rootNode, Leaf) or
                self.rootNode in self.getChildren)

        self.nodes = [ node for node, depth in self.breadthFirst() ]
        self.splitIds = [ node
                          for node in self.nodes
                          if not isinstance(node, Leaf) ]
        assert len(self.splitIds) <= len(splitInfos)
        if len(self.splitIds) < len(splitInfos):
            raise RuntimeError('there appear to be unreachable nodes')
        self.leaves = [ node
                        for node in self.nodes
                        if isinstance(node, Leaf) ]
        assert len(self.leaves) == len(self.splitIds) + 1

    def breadthFirst(self, nodeStart = None):
        """Returns an iterator over nodes in the tree in breadth-first order.

        Each element of the returned iterator is a pair of a node and its
        depth.
        """
        if nodeStart is None:
            nodeStart = self.rootNode
        agenda = deque([(nodeStart, 0)])
        while agenda:
            node, depth = agenda.popleft()
            yield node, depth
            if not isinstance(node, Leaf):
                for childNode in self.getChildren[node]:
                    agenda.append((childNode, depth + 1))

    def breadthFirstWithCIL(self, nodeStart = None):
        """Returns an iterator over nodes in the tree in breadth-first order.

        Each element of the returned iterator is a pair of a node and the
        sequence of child indices corresponding to the path taken in the tree
        to get to that node.
        """
        if nodeStart is None:
            nodeStart = self.rootNode
        agenda = deque([(nodeStart, [])])
        while agenda:
            node, childIndexList = agenda.popleft()
            yield node, childIndexList
            if not isinstance(node, Leaf):
                for childIndex, childNode in enumerate(self.getChildren[node]):
                    childIndexListNew = list(childIndexList)
                    childIndexListNew.append(childIndex)
                    agenda.append((childNode, childIndexListNew))

# (FIXME : "navigable" is a horrible term for this and concept seems bad too)
class NavBinaryTree(object):
    """A "navigable" binary decision tree.

    "Navigable" here means that the tree knows the "meaning" of its questions,
    so we can navigate the tree for a given label.

    Each internal node in the tree should have two children, with the first
    child corresponding to a "no" answer to that node's question and the second
    child corresponding to a "yes" answer.
    """
    def __init__(self, quesReDict, tree):
        self.quesReDict = quesReDict
        self.tree = tree

        for node in self.tree.splitIds:
            assert len(self.tree.getChildren[node]) == 2

    def getLeaf(self, label):
        """Returns the leaf associated with a label."""
        node = self.tree.rootNode
        while not isinstance(node, Leaf):
            quesId = self.tree.getQuesId[node]
            children = self.tree.getChildren[node]
            quesRe = self.quesReDict[quesId]
            node = children[1] if quesRe.match(label) else children[0]

        return node

def readTreeFileLines(treeFileLines):
    questions, treeFileLines = qio.parseQuestionLines(
        treeFileLines, isTreeFile=True
    )

    streamSpecedTrees = []

    currStreamSpec = None
    currSplitInfos = None

    for line in treeFileLines:
        line = line.strip()
        fields = line.split()
        if len(fields) > 0:
            assert fields[0] != 'QS'

            if currStreamSpec is None:
                assert len(fields) == 1
                assert currSplitInfos is None
                currStreamSpec = fields[0]
            elif fields[0] == '{':
                assert len(fields) == 1
                assert currStreamSpec is not None
                assert currSplitInfos is None
                currSplitInfos = []
            elif fields[0] == '}':
                assert len(fields) == 1
                assert currStreamSpec is not None
                assert currSplitInfos is not None
                streamSpecedTrees.append((
                    currStreamSpec,
                    Tree(currSplitInfos, rootNode = 0)
                ))
                currStreamSpec = None
                currSplitInfos = None
            elif len(fields) == 1 and fields[0][0] == '"':
                # degenerate tree with just a root leaf
                assert currStreamSpec is not None
                assert currSplitInfos is None
                currSplitInfos = []
                macroId = stripQuotes(fields[0])
                streamSpecedTrees.append((
                    currStreamSpec,
                    Tree(currSplitInfos, rootNode = Leaf(macroId))
                ))
                currStreamSpec = None
                currSplitInfos = None
            else:
                assert len(fields) == 4
                assert currStreamSpec is not None
                assert currSplitInfos is not None
                splitId = int(fields[0])
                quesId = fields[1]
                if fields[2][0] == '"':
                    macroId = stripQuotes(fields[2])
                    leftChild = Leaf(macroId)
                else:
                    leftChild = int(fields[2])
                if fields[3][0] == '"':
                    macroId = stripQuotes(fields[3])
                    rightChild = Leaf(macroId)
                else:
                    rightChild = int(fields[3])
                currSplitInfos.append((
                    splitId, quesId,
                    leftChild, rightChild
                ))

    quesIdsSet = set([ quesId for quesId, _ in questions ])
    assert len(quesIdsSet) == len(questions)
    for streamSpec, tree in streamSpecedTrees:
        for splitId in tree.splitIds:
            quesId = tree.getQuesId[splitId]
            assert quesId in quesIdsSet

    return questions, streamSpecedTrees

def writeTreeFileLines(questions, streamSpecedTrees):
    outLines = list(qio.writeQuestionLines(questions, isTreeFile=True))
    for streamSpec, tree in streamSpecedTrees:
        outLines.append('')
        outLines.append(' %s' % streamSpec)
        if isinstance(tree.rootNode, Leaf):
            # degenerate tree with just a root leaf
            outLines.append(' %s' % tree.rootNode)
        else:
            outLines.append('{')
            for splitId in tree.splitIdsInOrigOrder:
                quesId = tree.getQuesId[splitId]
                leftChild, rightChild = tree.getChildren[splitId]
                outLines.append(
                    ' %s %s %s %s' %
                    (splitId, quesId, leftChild, rightChild)
                )
            outLines.append('}')
    outLines.append('')
    return outLines

def readTreeFile(treeFile):
    """Reads a decision tree file."""
    lines = [ line.rstrip('\n') for line in open(treeFile, 'U') ]
    questions, streamSpecedTrees = readTreeFileLines(lines)
    return questions, streamSpecedTrees

def readTreeFileVerifying(treeFile):
    """Reads a decision tree file and verifies that it was read correctly.

    Verifies that reconstructing the decision tree file from the parsed output
    reproduces the original decision tree file up to certain whitespace
    substitutions.
    """
    lines = [ line.rstrip('\n') for line in open(treeFile, 'U') ]
    questions, streamSpecedTrees = verifiedRead(
        readTreeFileLines, writeTreeFileLines, lines, unpack=True
    )
    return questions, streamSpecedTrees

def writeTreeFile(questions, streamSpecedTrees, treeFile):
    """Writes a decision tree file."""
    lines = writeTreeFileLines(questions, streamSpecedTrees)
    with open(treeFile, 'w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')
