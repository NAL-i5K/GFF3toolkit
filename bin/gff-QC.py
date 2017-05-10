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
import ERROR # Details of the errors that can be detected.

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
    
    Testing environment:
    1. Python 2.7

    Inputs:
    1. GFF3: Specify the file name with the -g or --gff argument; Please note that this program requires gene/pseudogene and mRNA/pseudogenic_transcirpt to have an ID attribute in column 9. 
    2. fasta file: Specify the file name with the -f or --fasta argument

    Outputs:
    1. Error report for the input GFF3 file.

    Quick start:
    python2.7 GFF3toolkit/bin/gff-QC.py -g small_files/annotations2.gff -f small_files/sample.fa -o test
    or
    python2.7 GFF3toolkit/bin/gff-QC.py --gff small_files/annotations2.gff --fasta small_files/sample.fa --output test

    """))
    parser.add_argument('-g', '--gff', type=str, help='Genome annotation file, gff3 format') 
    parser.add_argument('-f', '--fasta', type=str, help='Genome sequences, fasta format')
    parser.add_argument('-o', '--output', type=str, help='output file name (default: report.txt)')
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



    logger_stderr.info('Reading gff files: (%s)...\n', args.gff)
    gff3 = Gff3(gff_file=args.gff, fasta_external=args.fasta, logger=logger_null)
    logger_stderr.info('Checking errors in the gff files: (%s)...\n', args.gff)
    if not gff3.check_parent_boundary():
        sys.exit()

    gff3.check_unresolved_parents()
    gff3.check_phase()
    gff3.check_reference()
    logger_stderr.info('\t- Checking missing attributes: (%s)...\n', 'function4gff.FIX_MISSING_ATTR()')
    function4gff.FIX_MISSING_ATTR(gff3)

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
    if single_feature.main(gff3, logger=logger_stderr):
        error_set.extend(single_feature.main(gff3, logger=logger_stderr))

    if args.output:
        logger_stderr.info('Print QC report at {0:s}'.format(args.output))
        report_fh = open(args.output, 'wb')
    else:
        logger_stderr.info('Print QC report at {0:s}'.format('report.txt'))
        report_fh = open('report.txt', 'wb')


    ERROR_INFO = ERROR.INFO

    report_fh.write('Line_num\tID\tError_code\tError_tag\n')
    for e in error_set:
        tag = '[{0:s}]'.format(e['eTag'])
        report_fh.write('{0:s}\t{1:s}\t{2:s}\t{3:s}\n'.format(str(e['line_num']),str(e['ID']), str(e['eCode']), str(tag)))
