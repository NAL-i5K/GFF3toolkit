#! /usr/local/bin/python2.7
import sys
import re
import logging
from gff3tool.lib.gff3 import Gff3
import gff3tool.lib.gff3_merge as gff3_merge
from gff3tool.bin import version

__version__ = version.__version__

def check_replace(gff, user_defined1=None):
    if user_defined1 is not None:
        u_type = set()
        for line in user_defined1:
            u_type.add(line[0])

    roots = []
    error_lines = list()
    for line in gff.lines:
        if not user_defined1:
            try:
                if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                   roots.append(line)
            except KeyError:
                print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
        else:
            if line['type'] in u_type:
                try:
                    if not line['attributes'].has_key('replace'):
                        error_lines.append(line)
                except KeyError:
                    print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))

    #roots = [line for line in gff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]

    for root in roots:
        children = root['children']
        for child in children:
            if not child['attributes'].has_key('replace'):
                error_lines.append(child)

    if len(error_lines):
        return error_lines
    else:
        return False


def main(gff_file1, gff_file2, fasta, report, output_gff, all_assign=False, auto=True, user_defined1=None, user_defined2=None, logger=None):
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)

    if not logger:
        logger = logger_null

    if re.search(r'(\S+)/(\S+)$',gff_file1):
        _, gff_file1_name = re.search(r'(\S+)/(\S+)$',gff_file1).groups()
    else:
        gff_file1_name = gff_file1
#    print(path, gff_file1_name)

    if auto:
        autoDIR = 'auto_replace_tag'
        autoFILE = '{0:s}/check1.txt'.format(autoDIR)
        autoReviseGff = '{0:s}/Revised_{1:s}'.format(autoDIR, gff_file1_name)
        autoReviseReport = '{0:s}/replace_tag_report.txt'.format(autoDIR)

        logger.info('========== Auto-assignment of replace tags for each transcript model ==========')
        gff3_merge.auto_replace_tag.main(gff1=gff_file1, gff2=gff_file2, fasta=fasta, outdir=autoDIR, scode='TEMP', all_assign=all_assign, user_defined1=user_defined1, user_defined2=user_defined2, logger=logger)
        gff3_merge.revision.main(gff_file=gff_file1, revision_file=autoFILE, output_gff=autoReviseGff, report_file=autoReviseReport, user_defined1=user_defined1, auto=auto, logger=logger)

        logger.info('========== Check whether there are missing replace tags ==========')
        gff3 = Gff3(gff_file=autoReviseGff, logger=logger_null)
        error_models = check_replace(gff3, user_defined1)
        if error_models:
            logger.error('There are models missing replace tags...')
            logger.error('Please check the below models in {0:s}. Please specify the proper replaced models at colulumn 9. For example, \'replace=[Transcript ID]\'. If this is a newly added model, please put it as \'replace=NA\'. Then, re-excute the program.\n'.format(autoReviseGff))
            for line in error_models:
                print(line['line_raw'])
            return
        else:
            logger.info('- All models have replace tags.')

        logger.info('========== Merge the two gff files ==========')
        gff3_merge.merge.main(autoReviseGff, gff_file2, output_gff, report, user_defined1, user_defined2, logger)
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
        gff3_merge.merge.main(gff_file1, gff_file2, output_gff, report, user_defined1, user_defined2, logger)


def script_main():
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
    1. GFF3 file 1: Gff with annotations modified relative to the original gff (e.g. output from the Apollo program), specify the file name with the -g1 argument
    2. GFF3 file 2: Original/Reference gff, specify the file name with the -g2 argument
    3. FASTA: Genomic sequences in the FASTA format with the -f argument

    Outputs:
    1. Merged GFF3: Models from GFF3 file 1 replace Models from GFF3 file 2 based on their replace tag. Specify the output file name with the -og argument
    2. Log report for the integration: specify the file name with the -r argument

    Examples:
    1. Specify the input, output file names and options using short arguments:
       gff3_merge -g1 example_file/new_models.gff3 -g2 example_file/reference.gff3 -f example_file/reference.fa -og merged.gff -r merged_report.txt
    2. Specify the input, output file names and options using long arguments:
       gff3_merge --gff_file1 example_file/new_models.gff3 --gff_file2 example_file/reference.gff3 --fasta example_file/reference.fa --output_gff merged.gff --report_file merged_report.txt


    """))
    parser.add_argument('-g1', '--gff_file1', type=str, help='Updated GFF3 file, such as Apollo gff')
    parser.add_argument('-g2', '--gff_file2', type=str, help='Reference GFF3 file, such as Maker gff or OGS gff')
    parser.add_argument('-f', '--fasta', type=str, help='Genomic sequences in the fasta format')
    parser.add_argument('-u1', '--user_defined_file1', type=str, help='File for specifing parent and child features for fasta extraction from updated GFF3 file.')
    parser.add_argument('-u2', '--user_defined_file2', type=str, help='File for specifing parent and child features for fasta extraction from reference GFF3 file.')
    parser.add_argument('-og', '--output_gff', type=str, help='The merged GFF3 file')
    parser.add_argument('-r', '--report_file', type=str, help='Log file for the integration')
    parser.add_argument('-a', '--all', action='store_true', help='auto-assignment replace tags for all transcript features. (default: Only automatically assign replace tags for the transcript without replace tags)')
    parser.add_argument('-noAuto', '--auto_assignment', action='store_false', help='Turn off the auto-assignment of replace tags, if you already have replace tags in your updated gff (default: Automatically assign replace tags and then merge the gff files)')
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

    if args.user_defined_file1:
        logger_stderr.info('Checking user defined file1 (%s)...', args.user_defined_file1)
        user_defined1 = []
        try:
            with open(args.user_defined_file1, "r") as ud:
                for line in ud:
                    line = line.strip()
                    lines = line.split(" ")
                    if len(lines) != 2:
                        logger_stderr.error('Please specify parent and child feature follow the format: [parent feature type] [child feature type] in (%s)', args.user_defined_file1)
                    else:
                        if lines not in user_defined1:
                            user_defined1.append(lines)
            if len(user_defined1) == 0:
                logger_stderr.error('Failed to get parent and child feature from (%s). Please specify parent and child feature follow the format: [parent feature type] [child feature type]', args.user_defined_file1)
            args.user_defined_file1 = user_defined1
        except:
            parser.print_help()
            sys.exit(1)


    if args.user_defined_file2:
        logger_stderr.info('Checking user defined file2 (%s)...', args.user_defined_file2)
        user_defined2 = []
        try:
            with open(args.user_defined_file2, "r") as ud:
                for line in ud:
                    line = line.strip()
                    lines = line.split(" ")
                    if len(lines) != 2:
                        logger_stderr.error('Please specify parent and child feature follow the format: [parent feature type] [child feature type] in (%s)', args.user_defined_file2)
                    else:
                        if lines not in user_defined2:
                            user_defined2.append(lines)
            if len(user_defined2) == 0:
                logger_stderr.error('Failed to get parent and child feature from (%s). Please specify parent and child feature follow the format: [parent feature type] [child feature type]', args.user_defined_file2)
            args.user_defined_file2 = user_defined2
        except:
            parser.print_help()
            sys.exit(1)

    if args.all and not args.auto_assignment:
        logger_stderr.error('-a and -noAuto specify opposite behaviors, only one of the two arguments can be accepted.')
        sys.exit(0)
    if args.report_file:
        logger_stderr.info('Writing validation report (%s)...\n', args.report_file)
        report_fh = open(args.report_file, 'wb')
    else:
        report_fh = open('merge_report.txt', 'wb')

    if not args.output_gff:
        args.output_gff='merged.gff'

    main(args.gff_file1, args.gff_file2, args.fasta, report_fh, args.output_gff, args.all, args.auto_assignment, args.user_defined_file1, args.user_defined_file2, logger=logger_stderr)
