# -*- coding: utf-8 -*-
"""Extract sequences from specific regions of genome based on gff file."""
from __future__ import absolute_import
import .gff3_to_fasta 

VERSION = (0, 0, 1)
__version__ = '.'.join(map(str, VERSION[0:3])) + ''.join(VERSION[3:])
__author__ = 'Mei-Ju May Chen'
__email__ = 'arbula [at] gmail [dot] com'
__homepage__ = ''
__docformat__ = 'restructuredtext'
