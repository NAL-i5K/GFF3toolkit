# -*- coding: utf-8 -*-
"""Manipulate genomic features and validate the syntax and reference sequence of your GFF3 files"""
from __future__ import absolute_import
from .gff3 import Gff3
__all__ = ['Gff3']

VERSION = (0, 4, 1)
__version__ = '.'.join(map(str, VERSION[0:3])) + ''.join(VERSION[3:])
__author__ = 'Han Lin'
__email__ = 'hotdogee [at] gmail [dot] com'
__contributor = 'Mei-Ju May Chen'
__c_email__ = 'arbula [at] gmail [dot] com'
__homepage__ = 'https://github.com/hotdogee/gff3-py'
__docformat__ = 'restructuredtext'
