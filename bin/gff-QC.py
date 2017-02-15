#! /usr/local/bin/python2.7
# Contributed by Mei-Ju May Chen <arbula [at] gmail [dot] com> (2015)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import sys
import re
import logging
# try to import from project first
from os.path import dirname
if dirname(__file__) == '':
    lib_path = '../lib'
else:
    lib_path = dirname(__file__) + '/../lib'
sys.path.insert(1, lib_path)
from gff3_modified import Gff3
import function4gff
import single_feature
import inter_model
import intra_model

__version__ = '0.0.1'

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
    
    Testing enviroment:
    1. Python 2.7

    Inputs:
    1. GFF3: reads from STDIN by default, may specify the file name with the -g argument
    2. fasta file: reads from STDIN by default, may specify the file name with the -f argument

    Outputs:
    1. Extract sequences from specific regions of genome based on gff file.

    """))
    parser.add_argument('-g', '--gff', type=str, help='Genome annotation file, gff3 format (default: STDIN)') 
    parser.add_argument('-f', '--fasta', type=str, help='Genome sequences, fasta format (default: STDIN)')
    parser.add_argument('-sc', '--species_code', type=str, help='If the species is hosted by I5K Workspace@NAL, you can give the I5K species code to have a url link to Web Apollo in I5K Workspace@NAL. eg. "lepdec", which was abbreviated from Leptinotarsa decemlineata. (default: STDIN)')
    parser.add_argument('-o', '--output', type=str, help='output file name (default: STDIN)')
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

    if args.fasta:
        logger_stderr.info('Checking genome fasta (%s)...', args.fasta)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.fasta = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.species_code:
        logger_stderr.info('Specifying species code: (%s)...', args.species_code)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.species_code = sys.stdin
        logger_stderr.info('Reading from STDIN...')

    if args.output:
        logger_stderr.info('Specifying output file name: (%s)...\n', args.output)
        report_fh = open(args.output, 'wb')
    else:
        report_fh = open('report.txt', 'wb')


    #ERROR_CODE = ['Esf0001', 'Esf0002', 'Ema0005', 'Emr0001'] 
    #ERROR_TAG = ['pseudogene or not?', 'Negative/Zero start/end coordinate', 'unusual child features in the type of pseudogene found', 'Duplicate transcripts found']
    #ERROR_INFO = dict(zip(ERROR_CODE, ERROR_TAG))

    logger_stderr.info('Reading gff files: (%s)...\n', args.gff)
    gff3 = Gff3(gff_file=args.gff, fasta_external=args.fasta, logger=logger_null)
    logger_stderr.info('Checking errors in the gff files: (%s)...\n', args.gff)
    gff3.check_unresolved_parents()
    gff3.check_parent_boundary()
    gff3.check_phase()
    gff3.check_reference()
    logger_stderr.info('\t- Checking missing attributes: (%s)...\n', 'single_feature.FIX_MISSING_ATTR()')

    error_set = list()
    if function4gff.extract_internal_detected_errors(gff3):
        error_set.extend(function4gff.extract_internal_detected_errors(gff3))
    logger_stderr.info('\t- Checking intra-model errors: (%s)...\n', args.gff)
    if intra_model.main(gff3, logger=logger_stderr):
        error_set.extend(intra_model.main(gff3, logger=logger_stderr))
    logger_stderr.info('\t- Checking inter-model errors: (%s)...\n', args.gff)
    if inter_model.main(gff3, logger=logger_stderr):
        error_set.extend(inter_model.main(gff3, logger=logger_stderr))
    logger_stderr.info('\t- Checking single-feature errors: (%s)...\n', args.gff)
    if inter_model.main(gff3, logger=logger_stderr):
        error_set.extend(single_feature.main(gff3, logger=logger_stderr))

    if args.output:
        logger_stderr.info('Print QC report at {0:s}'.format(args.output))
    else:
        logger_stderr.info('Print QC report at {0:s}'.format('report.txt'))
    report_fh.write('ID\tError_code\tError_tag\n')
    for e in error_set:
        tag = '[{0:s}]'.format(e['eTag'])
        report_fh.write('{0:s}\t{1:s}\t{2:s}\n'.format(str(e['ID']), str(e['eCode']), str(tag)))
