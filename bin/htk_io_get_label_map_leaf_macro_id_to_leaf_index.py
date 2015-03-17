#!/usr/bin/python
"""Fixes a mapping from leaf macro id to leaf index for an HTK / HTS tree file.

For example, might map "mgc_s2_23" to "0".
"""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import sys
import argparse

import htk_io.tree as tio

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument(
        dest='treeFile', metavar='TREE',
        help='an HTK / HTS tree file (e.g. "mgc.inf")'
    )
    args = parser.parse_args(argv[1:])

    questions, streamSpecedTrees = tio.readTreeFileVerifying(args.treeFile)

    leafMacroIdSet = set()
    for streamSpec, tree in streamSpecedTrees:
        for leaf in tree.leaves:
            leafMacroIdSet.add(leaf.macroId)

    for leafIndex, leafMacroId in enumerate(sorted(leafMacroIdSet)):
        print '%s %s' % (leafMacroId, leafIndex)

if __name__ == '__main__':
    main(sys.argv)
