htk_io
======

This python package allows reading and writing of files in some of the formats
used by `Hidden Markov Model Toolkit (HTK) <http://htk.eng.cam.ac.uk/>`_ and
`HMM-based Speech Synthesis System (HTS) <http://hts.sp.nitech.ac.jp/>`_.
The following HTK / HTS file formats are currently supported:

- alignment files (also known as "label" files)
- decision tree question set files
- decision tree files
- raw vector sequence files, used by HTS for storing speech parameter sequences

Alignments, trees, etc are represented in memory using simple python data
structures.
Files in the above formats may be read into, or written from, these python
representations.

License
-------

Please see the file ``License`` for details of the license and warranty for
htk_io.

Installation
------------

For most purposes the simplest way to install htk_io is to use pip.
For example in Debian and Ubuntu::

    sudo apt-get install python-numpy
    sudo pip install htk_io

The first command installs numpy from the system repository, since installing
numpy using pip is generally not recommended.
The second command installs the latest released version of
`htk_io on PyPI <https://pypi.python.org/pypi/htk_io>`_, together with any
currently uninstalled python packages required by htk_io.

htk_io can also be installed in a virtualenv::

    sudo apt-get install python-numpy
    virtualenv --system-site-packages env
    env/bin/pip install htk_io

The latest development version of htk_io is available from a github repository
(see below).

To check that htk_io is installed correctly you can run the test suite::

    python -m unittest discover htk_io

Usage
-----

Examples of usage of various functions and classes are included in their
docstrings.
A few examples of files in the formats this package can read and write are
provided in the ``example`` directory.

Source
------

The source code is hosted in the
`htk_io github repository <https://github.com/MattShannon/htk_io>`_.
To obtain the latest source code using git::

    git clone git://github.com/MattShannon/htk_io.git

Development is in fact done using `darcs <http://darcs.net/>`_, with the darcs
repository converted to a git repository using
`darcs-to-git <https://github.com/purcell/darcs-to-git>`_.

To install any currently uninstalled python packages required by htk_io::

    sudo apt-get install cython python-numpy
    sudo pip install -r requirements.txt

Bugs
----

Please use the `issue tracker <https://github.com/MattShannon/htk_io/issues>`_
to submit bug reports.

Contact
-------

The author of htk_io is `Matt Shannon <mailto:matt.shannon@cantab.net>`_.
