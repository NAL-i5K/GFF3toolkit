#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
# Contributed by Mei-Ju May Chen <arbula [at] gmail [dot] com> (2016)

"""
QC functions for processing every single feature in GFF3 file.
"""
from __future__ import print_function

#from collections import OrderedDict # not available in 2.6
from itertools import groupby
try:
    from urllib import quote, unquote
except ImportError:
    from urllib.parse import quote, unquote
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
from gff3 import Gff3
import function4gff
import ERROR

__version__ = '0.0.1'

ERROR_INFO = ERROR.INFO

def FIX_PSEUDOGENE(gff):
    roots = []
    for line in gff.lines:
        try:
            if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                if len(line['attributes']) != 0:
                    roots.append(line)
                else:
                    print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
        except KeyError:
            print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))


    #roots = [line for line in gff.lines if line['line_type']=='feature' and not line['attributes'].has_key('Parent')]
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
    try:
        for v in line['attributes'].itervalues():
            if re.search(r"[Pp][Ss][EUeu][EUeu][Dd][Oo][Gg][Ee][Nn]*", str(v)):
                flag += 1
        if flag and not re.search(r"pseudogen*", line['type']):
            result['ID'] = [line['attributes']['ID']]
            result['line_num'] = ['Line {0:s}'.format(str(line['line_index'] + 1))]
            result['eCode'] = eCode
            result['eLines'] = [line]
            result['eTag'] = ERROR_INFO[eCode]
            gff.add_line_error(line, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})
    except:
        logger.error('Program dies at Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
    if len(result):
        return [result]

def check_strand(gff, line):
    eCode = 'Esf0003'
    result = dict()
    try:
        if line['strand'] is '+' or line['strand'] is '-':
            pass
        elif line['strand'] is '.' or line['strand'] is '?':
            result['ID'] = [line['attributes']['ID']]
            result['line_num'] = ['Line {0:s}'.format(str(line['line_index'] + 1))]
            result['eCode'] = eCode
            result['eLines'] = [line]
            result['eTag'] = '{0:s}: legal chacracter, "{1:s}", found at the strand field'.format(ERROR_INFO[eCode], line['strand'])
            gff.add_line_error(line, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})
        else:
            result['ID'] = [line['attributes']['ID']]
            result['line_num'] = ['Line {0:s}'.format(str(line['line_index'] + 1))]
            result['eCode'] = eCode
            result['eLines'] = [line]
            result['eTag'] = '{0:s}: illegal chacracter, "{1:s}" found at the strand field'.format(ERROR_INFO[eCode], line['strand'])
            gff.add_line_error(line, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})
    except:
        logger.error('Program dies at Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
    if len(result):
        return [result]


def main(gff, logger=None):
    function4gff.FIX_MISSING_ATTR(gff, logger=logger)
    FIX_PSEUDOGENE(gff)


    features = [line for line in gff.lines if line['line_type']=='feature']
    error_set=list()
    for f in features:
        r = check_pseudogene(gff, f)
        if not r == None:
            error_set.extend(r)
        r = None
        r = check_strand(gff, f)
        if not r == None:
            error_set.extend(r)
        r = None

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
