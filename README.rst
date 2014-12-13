htk_io
======

This python package allows reading and writing of files in some of the formats
used by `Hidden Markov Model Toolkit (HTK) <http://htk.eng.cam.ac.uk/>`_ and
`HMM-based Speech Synthesis System (HTS) <http://hts.sp.nitech.ac.jp/>`_.
For example, HTK and HTS label files and decision trees can be read into memory
as python data structures, and python data structures can be written to disk as
HTK and HTS files.

License
-------

Please see the file ``License`` for details of the license and warranty for
htk_io.

Installation
------------

For most purposes the simplest way to install htk_io is to use pip::

    sudo pip install htk_io

This installs the latest released version of
`htk_io on PyPI <https://pypi.python.org/pypi/htk_io>`_.
Alternatively you can download htk_io from PyPI and install it using::

    sudo python setup.py install

The latest development version of htk_io is available from a github repository
(see below).

Usage
-----

A few examples are provided in the ``example`` directory.

License
-------

Please see the file ``License`` for details of the license and warranty for
htk_io.

Source
------

The source code is hosted in the
`htk_io github repository <https://github.com/MattShannon/htk_io>`_.
To obtain the latest source code using git::

    git clone git://github.com/MattShannon/htk_io.git

Development is in fact done using `darcs <http://darcs.net/>`_, with the darcs
repository converted to a git repository using
`darcs-to-git <https://github.com/purcell/darcs-to-git>`_.

Bugs
----

Please use the `issue tracker <https://github.com/MattShannon/htk_io/issues>`_
to submit bug reports.

Contact
-------

The author of htk_io is `Matt Shannon <mailto:matt.shannon@cantab.net>`_.
