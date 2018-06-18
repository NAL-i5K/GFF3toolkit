#! /usr/local/bin/python2.7
# Contributed by Mei-Ju May Chen <arbula [at] gmail [dot] com> (2015)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import sys
# try to import from project first
from os.path import dirname
if dirname(__file__) == '':
    lib_path = '../lib'
else:
    lib_path = dirname(__file__) + '/../lib'
sys.path.insert(1, lib_path)

__version__ = '0.0.1'

INFO = {
    'Ema0001': 'Parent feature start and end coordinates exceed those of child features',
    'Ema0002': 'Protein sequence contains internal stop codons',
    'Ema0003': 'This feature is not contained within the parent feature coordinates',
    'Ema0004': 'Incomplete gene feature that should contain at least one mRNA, exon, and CDS',
    'Ema0005': 'Pseudogene has invalid child feature type',
    'Ema0006': 'Wrong phase',
    'Ema0007': 'CDS and parent feature on different strands',
    'Ema0008': 'Warning for distinct isoforms that do not share any regions',
    'Ema0009': 'Incorrectly merged gene parent? Isoforms that do not share coding sequences are found',
    'Emr0001': 'Duplicate transcript found', # Error message has to be modified in lib/inter_model/inter_model.py
    'Emr0002': 'Incorrectly split gene parent?',
    'Emr0003': 'Duplicate ID',
    'Esf0001': 'Feature type may need to be changed to pseudogene',
    'Esf0002': 'Start/Stop is not a valid 1-based integer coordinate',
    'Esf0003': 'Strand information missing',
    'Esf0004': 'Seqid not found in any ##sequence-region',
    'Esf0005': 'Start is less than the ##sequence-region start',
    'Esf0006': 'End is greater than the ##sequence-region end',
    'Esf0007': 'Seqid not found in the embedded ##FASTA',
    'Esf0008': 'End is greater than the embedded ##FASTA sequence length',
    #'Esf0009': 'Found Ns in a feature using the embedded ##FASTA', # This error would be detected by the program as well, but the error message has to be modified in gff3.py
    'Esf0010': 'Seqid not found in the external FASTA file',
    'Esf0011': 'End is greater than the external FASTA sequence length',
    #'Esf0012': 'Found Ns in a feature using the external FASTA', # This error would be detected by the program as well, but the error message has to be modified in gff3.py
    'Esf0013': 'White chars not allowed at the start of a line',
    'Esf0014': '##gff-version" missing from the first line',
    'Esf0015': 'Expecting certain fields in the feature',
    'Esf0016': '##sequence-region seqid may only appear once',
    'Esf0017': 'Start/End is not a valid integer',
    'Esf0018': 'Start is not less than or equal to end',
    'Esf0019': 'Version is not "3"',
    'Esf0020': 'Version is not a valid integer',
    'Esf0021': 'Unknown directive',
    'Esf0022': 'Features should contain 9 fields',
    'Esf0023': 'Escape certain characters',
    'Esf0024': 'Score is not a valid floating point number',
    'Esf0025': 'Strand has illegal characters',
    'Esf0026': 'Phase is not 0, 1, or 2, or not a valid integer',
    'Esf0027': 'Phase is required for all CDS features',
    'Esf0028': 'Attributes must escape the percent (%) sign and any control characters',
    'Esf0029': 'Attributes must contain one and only one equal (=) sign',
    'Esf0030': 'Empty attribute tag',
    'Esf0031': 'Empty attribute value',
    'Esf0032': 'Found multiple attribute tags',
    'Esf0033': 'Found ", " in a attribute, possible unescaped',
    'Esf0034': 'Attribute has identical values (count, value)',
    'Esf0035': 'Attribute has unresolved forward reference',
    'Esf0036': 'Value of a attribute contains unescaped ","',
    'Esf0037': 'Target attribute should have 3 or 4 values',
    'Esf0038': 'Start/End value of Target attribute is not a valid integer coordinate',
    'Esf0039': 'Strand value of Target attribute has illegal characters',
    'Esf0040': 'Value of Is_circular attribute is not "true"',
    'Esf0041': 'Unknown reserved (uppercase) attribute'
}

