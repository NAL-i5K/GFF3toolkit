#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
# Contributed by Mei-Ju May Chen <arbula [at] gmail [dot] com> (2016)

"""
QC functions for processing every single feature in GFF3 file.
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
import function4gff

__version__ = '0.0.1'

ERROR_CODE = ['Esf0001', 'Esf0002']
ERROR_TAG = ['Feature type may need to be changed to pseudogene', '[Start/Stop] is not a valid 1-based integer coordinate: "[coordinate]"', ]
ERROR_INFO = dict(zip(ERROR_CODE, ERROR_TAG))

def FIX_PSEUDOGENE(gff):
    roots = [line for line in gff.lines if line['line_type']=='feature' and not line['attributes'].has_key('Parent')]
    for root in roots:
        if root['type'] == 'pseudogene':
            for child in root['children']:
                if child['type'] == 'mRNA' or child['type'] == 'transcript':
                    child['type'] = 'pseudogenic_transcript'
                for grandchild in child['children']:
                    if grandchild['type'] == 'CDS':
                        grandchild['line_status'] = 'removed'
                    elif grandchild['type'] == 'exon':
                        grandchild['type'] = 'pseudogenic_exon'
                    others = gff.collect_descendants(grandchild)
                    for other in others:
                        other['line_status'] = 'removed'

def check_pseudogene(gff, line):
    ''' 
    Note:
    1. This funtion should be only applied on a gff file that has been fixed by FIX_PSEUDOGENE function.
    2. This function should be only applied on loci/transcript level features.
    '''
    eCode = 'Esf0001'
    flag = 0
    result=dict()
    for k,v in line['attributes'].items():
        if re.search(r"[Pp][Ss][EUeu][EUeu][Dd][Oo][Gg][Ee][Nn]*", str(v)):
            flag += 1
    if flag and not re.search(r"pseudogen*", line['type']):
        result['ID'] = [line['attributes']['ID']]
        result['eCode'] = eCode
        result['eLines'] = [line]
        result['eTag'] = ERROR_INFO[eCode]
        gff.add_line_error(line, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})
    if len(result):
        return [result]

'''
def check_negative_zero_coordinate(gff, line):
    eCode = 'Esf0002'
    result=dict()
    if line['start'] <= 0 or line['end'] <= 0:
        result['ID'] = [line['attributes']['ID']]
        result['eCode'] = eCode
        result['eLines'] = [line]
        result['eTag'] = ERROR_INFO[eCode]
        gff.add_line_error(line, {'message': ERROR_INFO[eCode], 'error_type': 'FORMAT', 'eCode': eCode})
    if len(result):
        return [result]
'''

def main(gff, logger=None):
    function4gff.FIX_MISSING_ATTR(gff, logger=logger)
    FIX_PSEUDOGENE(gff)


    features = [line for line in gff.lines if line['line_type']=='feature']
    error_set=list()
    for f in features:
        r = check_pseudogene(gff, f)
        if not r == None:
            error_set.extend(r)
        '''
        r = check_negative_zero_coordinate(gff, f)
        if not r == None:
            error_set.extend(r)
        '''
    '''
    for e in error_set:
        tag = '[{0:s}]'.format(ERROR_INFO[e['eCode']]) 
        print(e['ID'], e['eCode'], tag)
    '''
    if len(error_set): 
        return(error_set)

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
    QC functions for processing every single feature in GFF3 file.
    
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
    main(gff3, logger=logger_stderr)
    if args.output:
        gff3.write(args.output)
