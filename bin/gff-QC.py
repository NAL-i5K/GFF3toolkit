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
import ERROR

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
    1. GFF3: Specify the file name with the -g or --gff argument; Please note that this program requires gene/pseudogene, mRNA/pseudogenic_transcirpt, and exon/pseudogenic_exon to have an ID attribute in column 9. For those features without IDs, it would automatically generate IDs based on the corresponding parent information. However, the ID generation would fail, if a feature has multiple parents.
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


    if args.output:
        logger_stderr.info('Specifying output file name: (%s)...\n', args.output)
        report_fh = open(args.output, 'wb')
    else:
        report_fh = open('report.txt', 'wb')


    #ERROR_CODE = ['Esf0001', 'Esf0002', 'Ema0005', 'Emr0001'] 
    #ERROR_TAG = ['pseudogene or not?', 'Negative/Zero start/end coordinate', 'unusual child features in the type of pseudogene found', 'Duplicate transcripts found']
    #ERROR_INFO = dict(zip(ERROR_CODE, ERROR_TAG))

    '''
    ERROR_INFO = {
        'Ema0001': 'Parent feature start and end coordinates exceed those of child features',
        'Ema0002': 'Protein sequence contains stop codons',
        #'Ema0003': 'This feature is not contained within the parent feature coordinates', # Error message has to be modified in gff3_modified.py
        'Ema0004': 'Incomplete gene feature that should contain at least one mRNA, exon, and CDS',
        'Ema0005': 'Pseudogene has invalid child feature type',
        #'Ema0006': 'Wrong phase', # Error message has to be modified in gff3_modified.py
        'Ema0007': 'CDS and parent feature on different strands',
        #'Emr0001': 'Duplicate transcript found', # Error message has to be modified in lib/inter_model/inter_model.py
        'Emr0002': 'Incorrectly merged gene parent?',
        'Emr0003': 'Incorrectly split gene parent?',
        'Emr0004': 'Isoforms that do not share coding sequence',
        #'Emr0005': 'Duplicate ID',
        'Esf0001': 'Feature type may need to be changed to pseudogene',
        #'Esf0002': '[Start/Stop] is not a valid 1-based integer coordinate: "[coordinate]"', # Error message has to be modified in gff3_modified.py
        'Esf0003': 'strand information missing',
        'Esf0004': 'Seqid not found in any ##sequence-region',
        'Esf0005': 'Start is less than the ##sequence-region start',
        'Esf0006': 'End is greater than the ##sequence-region end',
        'Esf0007': 'Seqid not found in the embedded ##FASTA',
        'Esf0008': 'End is greater than the embedded ##FASTA sequence length',
        #'Esf0009': 'Caution: [type] feature (length: [N]) contains [X] consecutive N\'s (start, length): ([Y], [X])', # Error message has to be modified in gff3_modified.py
        'Esf0010': 'Seqid not found in the external FASTA file',
        'Esf0011': 'End is greater than the external FASTA sequence length',
        #'Esf0012': 'Caution: [type] feature (length: [N]) contains [X] consecutive N\'s (start, length): ([Y], [X])', # Error message has to be modified in gff3_modified.py
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
        'Esf0023': 'escape certain characters',
        'Esf0024': 'Score is not a valid floating point number',
        'Esf0025': 'Strand has illegal characters',
        'Esf0026': 'Phase is not 0, 1, or 2, or not a valid integer',
        'Esf0027': 'Phase is required for all CDS features',
        'Esf0028': 'Attributes must escape the percent (%) sign and any control characters',
        'Esf0029': 'Attributes must contain one and only one equal (=) sign',
        #'Esf0030': 'Empty attribute tag',  # Error message has to be modified in gff3_modified.py
        #'Esf0031': 'Empty attribute value', # Error message has to be modified in gff3_modified.py
        #'Esf0032': 'Found multiple attribute tags',
        'Esf0033': 'Found ", " in a attribute, possible unescaped',
        #'Esf0034': 'attribute has identical values (count, value)', # Error message has to be modified in gff3_modified.py
        'Esf0035': 'attribute has unresolved forward reference',
        'Esf0036': 'Value of a attribute contains unescaped ","',
        'Esf0037': 'Target attribute should have 3 or 4 values',
        'Esf0038': 'Start/End value of Target attribute is not a valid integer coordinate',
        'Esf0039': 'Strand value of Target attribute has illegal characters',
        'Esf0040': 'Value of Is_circular attribute is not "true"',
        'Esf0041': 'Unknown reserved (uppercase) attribute'
    }
    '''

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

    ERROR_INFO = ERROR.INFO

    report_fh.write('ID\tError_code\tError_tag\n')
    for e in error_set:
        tag = '[{0:s}]'.format(e['eTag'])
        report_fh.write('{0:s}\t{1:s}\t{2:s}\n'.format(str(e['ID']), str(e['eCode']), str(tag)))
