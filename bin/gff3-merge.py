#! /usr/local/bin/python2.7
# Contributed by Mei-Ju Chen <arbula [at] gmail [dot] com> (2015)
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
import gff3_merge

__version__ = '0.0.5'

def check_replace(gff):
    roots = [line for line in gff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    error_lines = list()
    for root in roots:
        children = root['children']
        for child in children:
            if not child['attributes'].has_key('replace'):
                error_lines.append(child)
    
    if len(error_lines):
        return error_lines
    else:
        return False


def main(gff_file1, gff_file2, fasta, report, output_gff, auto=True, logger=None):
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)

    if not logger:
        logger = logger_null

    if re.search(r'(\S+)/(\S+)$',gff_file1):
        path, gff_file1_name = re.search(r'(\S+)/(\S+)$',gff_file1).groups()
    else:
        path = '.'
        gff_file1_name = gff_file1
#    print(path, gff_file1_name)

    if auto:
        autoDIR = 'auto_replace_tag'
        autoFILE = '{0:s}/check1.txt'.format(autoDIR)
        autoReviseGff = '{0:s}/Revised_{1:s}'.format(autoDIR, gff_file1_name)
        autoReviseReport = '{0:s}/replace_tag_report.txt'.format(autoDIR)

        logger.info('========== Auto-assignment of replace tags for each transcrip models ==========')
        gff3_merge.auto_replace_tag.main(gff_file1, gff_file2, fasta, autoDIR, 'TEMP', logger)
        gff3_merge.revision.main(gff_file1, autoFILE, autoReviseGff, autoReviseReport, logger)

        logger.info('========== Check whether there are missing replace tags ==========')
        gff3 = Gff3(gff_file=autoReviseGff, logger=logger_null)
        error_models = check_replace(gff3)
        if error_models:
            logger.error('There are models missing replace tags...')
            logger.error('Please check the below models in {0:s}. Please specify the proper replaced models at colulumn 9. For example, \'replace=[Transcript ID]\'. If this is a newly added model, please put it as \'replace=NA\'. Then, re-excute the program.\n'.format(autoReviseGff))
            for line in error_models:
                print(line['line_raw'])
            return
        else:
            logger.info('- All models have replace tags.')

        logger.info('========== Merge the two gff files ==========')
        gff3_merge.merge.main(autoReviseGff, gff_file2, output_gff, report, logger)
    else:
        logger.info('========== Check whether there are missing replace tags ==========')
        gff3 = Gff3(gff_file=gff_file1, logger=logger_null)
        error_models = check_replace(gff3)
        if error_models:
            logger.error('There are models missing replace tags...')
            logger.error('Please check the below models in {0:s}. Please specify the proper replaced models at colulumn 9. For example, \'replace=[Transcript ID]\'. If this is a newly added model, please put it as \'replace=NA\'. Then, re-excute the program.'.format(gff_file1))
            for line in error_models:
                print(line['line_raw'].strip())
            return
        else:
            logger.info('- All models have replace tags.')

        logger.info('========== Merge the two gff files ==========')
        gff3_merge.merge.main(gff_file1, gff_file2, output_gff, report, logger)


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
    Merge two gff files of the same genome into one. 

    Testing enviroment:
    1. Python 2.7

    Inputs:
    1. GFF3 file 1: Web apollo gff, specify the file name with the -g1 argument
    2. GFF3 file 2: The other gff, specify the file name with the -g2 argument
    3. FASTA: Genomic sequences in the FASTA format with the -f argument

    Outputs:
    1. Merged GFF3: WA models would be append to the end of predicted gff file and be assinged a ID based on the naming system of the predicted gff, specify the file name with the -og argument
    2. Log report for the integration: specify the file name with the -r argument

    Examples:
    1. Specify the input, output file names and options using short arguments:
       python2.7 bin/%(prog)s -g1 CPB_WA_test.gff -g2 LDEC.Models-NALmod.gff3 -og merged.gff -r merged_report.txt
    2. Specify the input, output file names and options using long arguments:
       python2.7 bin/%(prog)s --gff_file1 CPB_WA_test.gff --gff_file2 LDEC.Models-NALmod.gff3 --output_gff merged.gff --report_file merged_report.txt


    """))
    parser.add_argument('-g1', '--gff_file1', type=str, help='Update GFF3 file, such as Apollo gff')
    parser.add_argument('-g2', '--gff_file2', type=str, help='Reference GFF3 file, such as Maker gff or OGS gff')
    parser.add_argument('-f', '--fasta', type=str, help='Genomic sequences in the fasta format')
    parser.add_argument('-og', '--output_gff', type=str, help='The merged GFF3 file')
    parser.add_argument('-r', '--report_file', type=str, help='Log file for the intergration')
    parser.add_argument('-noAuto', '--auto_assignment', action='store_false', help='Turn off the auto-assignemnt of replace tags, if you have had the replace tags in your update gff (default: Automatically assign replace tags and then merge the gff files)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
   
    args = parser.parse_args()

    if args.gff_file1:
        logger_stderr.info('Checking Update GFF3 file (%s)...', args.gff_file1)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.gff_file1 = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.gff_file2:
        logger_stderr.info('Checking Reference GFF3 file (%s)...', args.gff_file2)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.gff_file2 = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(2)

    if args.fasta:
        logger_stderr.info('Checking genome fasta (%s)...', args.fasta)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.fasta = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.report_file:
        logger_stderr.info('Writing validation report (%s)...\n', args.report_file)
        report_fh = open(args.report_file, 'wb')
    else:
        report_fh = open('merge_report.txt', 'wb')

    if not args.output_gff:
        args.output_gff='merged.gff'

    main(args.gff_file1, args.gff_file2, args.fasta, report_fh, args.output_gff, args.auto_assignment, logger=logger_stderr)
