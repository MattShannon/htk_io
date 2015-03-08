"""Common functions and classes for I/O."""

# Copyright 2014, 2015 Matt Shannon

# This file is part of htk_io.
# See `License` for details of license and warranty.

import os

class Io(object):
    """An abstract class for reading and writing files."""
    pass

class LineIo(Io):
    """An abstract class for reading and writing line-based files."""
    def writeFile(self, filename, obj):
        lines = self.writeLines(obj)
        with open(filename, 'w') as f:
            for line in lines:
                f.write(line)
                f.write('\n')

    def readFile(self, filename):
        lines = [ line.rstrip('\n') for line in open(filename, 'U') ]
        return self.readLines(lines)

# (FIXME : add corresponding write method and rename class
#    (after deciding how to encode general invertible transforms nicely))
class DirReader(object):
    """This class reads files with a common extension from a directory.

    An instance of this class can be used as a function from file base name to
    object.
    For a given base name, the object returned is read using `io` from the file
    in directory `readDir` with extension `ext`.

    Example usage (assumes the current directory contains the "example"
    subdirectory included in source code for this package):

    >>> from htk_io.base import DirReader
    >>> import htk_io.alignment as alio
    >>> alignmentIo = alio.AlignmentIo(framePeriod=0.005)
    >>> getAlignment = DirReader(alignmentIo, 'example', 'lab')
    >>> getAlignment('simple') == [
    ...     (0, 10, 'apple', None),
    ...     (10, 41, 'pears', None),
    ... ]
    True

    For a 2-level alignment:

    >>> getAlignment('simple-2-level') == [
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

    >>> alignmentIo2 = alio.AlignmentIo(framePeriod=1.0)
    >>> getAlignment2 = DirReader(alignmentIo2, 'example', 'lab')
    >>> getAlignment2('example-3-level') == [
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
    def __init__(self, io, readDir, ext, transform=None):
        self.io = io
        self.readDir = readDir
        self.ext = ext
        self.transform = transform

    def __call__(self, base):
        objFile = os.path.join(self.readDir, '%s.%s' % (base, self.ext))
        obj = self.io.readFile(objFile)
        if self.transform is not None:
            obj = self.transform(obj)
        return obj
