#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
# Contributed by Mei-Ju May Chen <arbula [at] gmail [dot] com> (2016)

"""
QC functions for processing multiple features between models (inter-model) in GFF3 file.
"""
from __future__ import print_function

#from collections import OrderedDict # not available in 2.6
from collections import defaultdict
from itertools import groupby
try:
    from urllib import quote, unquote
except ImportError:
    from urllib.parse import quote, unquote
from textwrap import wrap
import sys
import re
import logging
logger = logging.getLogger(__name__)
#log.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)
from os.path import dirname
if dirname(__file__) == '':
    lib_path = '../../lib'
else:
    lib_path = dirname(__file__) + '/../../lib'
sys.path.insert(1, lib_path)
from gff3_modified import Gff3

__version__ = '0.0.1'

def FIX_MISSING_ATTR(gff): 
    features = [line for line in gff.lines if line['line_type']=='feature']
    flag = 0
    for f in features:
        if not f['attributes'].has_key('owner'):
            f['attributes']['owner'] = 'Unassigned'
        if not f['attributes'].has_key('ID'):
            IDrequired = ['gene', 'pseudogene', 'mRNA', 'pseudogenic_transcript', 'exon', 'pseudogenic_exon']
            if f['type'] in IDrequired:
                logger_stderr.error('[Missing ID] A model needs to have a unique ID, but not. Please fix it first.\n{0:s}'.format(f['line_raw']))
                flag += 1
            else:
                if len(f['parents'])== 1 and len(f['parents'][0]) == 1:
                    tid = f['parents'][0][0]['attributes']['ID'] + '-' + f['type']
                    f['attributes']['ID'] = tid
                else:
                    logger_stderr.error('[Missing ID] The program try to automatically generate ID for this model, but failed becuase this model has multiple parent features.\n{0:s}'.format(f['line_raw']))
    if flag != 0:
        sys.exit()

def test(gff, line):
    eCode = ''
    result = dict()
    '''
    code here

    '''
    if len(result):
        return result


def main(gff):
    FIX_MISSING_ATTR(gff3)

    ERROR_CODE = ['']
    ERROR_TAG = ['[]']
    ERROR_INFO = dict(zip(ERROR_CODE, ERROR_TAG))

    roots = [line for line in gff.lines if line['line_type']=='feature' and not line['attributes'].has_key('Parent')]
    error_set=dict()
    for root in roots:
        r = test(gff, root)
        if not r == None:
            error_set = dict(error_set.items() + r.items())

    for k,v in error_set.items():
        print(k, v, ERROR_INFO[v])
    


if __name__ == '__main__':
    logger_stderr = logging.getLogger(__name__+'stderr')
    logger_stderr.setLevel(logging.INFO)
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger_stderr.addHandler(stderr_handler)
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)
    import argparse
    from textwrap import dedent
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=dedent("""\
    QC functions for processing multiple features between models (inter-model) in GFF3 file.
    
    Testing enviroment:
    1. Python 2.7

    Inputs:
    1. GFF3: reads from STDIN by default, may specify the file name with the -g argument

    Outputs:
    1. GFF3: fixed GFF file

    """))
    parser.add_argument('-g', '--gff', type=str, help='Summary Report from Monica (default: STDIN)') 
    parser.add_argument('-o', '--output', type=str, help='Output file name (default: STDIN)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    
    args = parser.parse_args()

    if args.gff:
        logger_stderr.info('Checking gff file (%s)...', args.gff)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.gff = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.output:
        logger_stderr.info('Specifying output file name: (%s)...\n', args.output)
        report_fh = open(args.output, 'wb')
    
    gff3 = Gff3(gff_file=args.gff, logger=logger_null)
    main(gff3)
