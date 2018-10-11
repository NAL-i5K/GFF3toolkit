#! /usr/local/bin/python2.7
import sys
import logging
from gff3tool.lib.gff3 import Gff3
import gff3tool.lib.function4gff as function4gff
import gff3tool.lib.single_feature as single_feature
import gff3tool.lib.inter_model as inter_model
import gff3tool.lib.intra_model as intra_model
import gff3tool.lib.ERROR as ERROR
from gff3tool.bin import version

__version__ = version.__version__


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

    Testing environment:
    1. Python 2.7

    Inputs:
    1. GFF3: Specify the file name with the -g or --gff argument; Please note that this program requires gene/pseudogene and mRNA/pseudogenic_transcript to have an ID attribute in column 9.
    2. fasta file: Specify the file name with the -f or --fasta argument

    Outputs:
    1. Error report for the input GFF3 file
	* Line_num: Line numbers of the found problematic models in the input GFF3 file.
	* Error_code: Error codes for the found problematic models. Please refer to lib/ERROR/ERROR.py to see the full list of Error_code and the corresponding Error_tag.
        * Error_tag: Detail of the found errors for the problematic models. Please refer to lib/ERROR/ERROR.py to see the full list of Error_code and the corresponding Error_tag.

    Quick start:
    gff3_QC -g example_file/example.gff3 -f example_file/reference.fa -o test
    or
    gff3_QC --gff example_file/example.gff3 --fasta example_file/reference.fa --output test

    """))
    parser.add_argument('-g', '--gff', type=str, help='Genome annotation file, gff3 format')
    parser.add_argument('-f', '--fasta', type=str, help='Genome sequences, fasta format')
    parser.add_argument('-noncg', '--noncanonical_gene', action="store_true", help='gff3 file is not formatted in the canonical gene model format.')
    parser.add_argument('-i', '--initial_phase', action="store_true", help='Check whether initial CDS phase is 0 (default: no check)')
    parser.add_argument('-n', '--allowed_num_of_n', type=int, default=0, help='Max number of Ns allowed in a feature, anything more will be reported as an error (default: 0)')
    parser.add_argument('-t', '--check_n_feature_types', nargs='*', default=['CDS'], help='Count the number of Ns in each feature with the type specified, multiple types may be specified, ex: -t CDS exon (default: "CDS")')
    parser.add_argument('-o', '--output', type=str, help='output file name (default: report.txt)')
    parser.add_argument('-s', '--statistic', type=str, help='statistic file name (default: statistic.txt)')
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
    if args.allowed_num_of_n or args.check_n_feature_types:
        check_n = True
    else:
        check_n = False

    logger_stderr.info('Reading gff files: (%s)...\n', args.gff)
    gff3 = Gff3(gff_file=args.gff, fasta_external=args.fasta, logger=logger_null)
    logger_stderr.info('Checking errors in the gff files: (%s)...\n', args.gff)
    if not gff3.check_parent_boundary():
        sys.exit()
    gff3.check_unresolved_parents()
    if args.noncanonical_gene == False:
        gff3.check_phase(args.initial_phase)
    gff3.check_reference(check_n=check_n, allowed_num_of_n=args.allowed_num_of_n, feature_types=args.check_n_feature_types)
    logger_stderr.info('\t- Checking missing attributes: (%s)...\n', 'function4gff.FIX_MISSING_ATTR()')
    function4gff.FIX_MISSING_ATTR(gff3, logger=logger_stderr)

    error_set = list()
    cmd = None
    cmd = function4gff.extract_internal_detected_errors(gff3)
    if cmd:
        error_set.extend(cmd)
    cmd = None
    logger_stderr.info('\t- Checking intra-model errors: (%s)...\n', args.gff)
    cmd = intra_model.main(gff3, logger=logger_stderr, noncanonical_gene=args.noncanonical_gene)
    if cmd:
        error_set.extend(cmd)
    cmd = None
    logger_stderr.info('\t- Checking inter-model errors: (%s)...\n', args.gff)
    cmd = inter_model.main(gff3, args.gff, args.fasta, logger=logger_stderr, noncanonical_gene=args.noncanonical_gene)
    if cmd:
        error_set.extend(cmd)
    cmd = None
    logger_stderr.info('\t- Checking single-feature errors: (%s)...\n', args.gff)
    cmd = single_feature.main(gff3, logger=logger_stderr)
    if cmd:
        error_set.extend(cmd)
    if args.output:
        logger_stderr.info('Print QC report at {0:s}'.format(args.output))
        report_fh = open(args.output, 'wb')
    else:
        logger_stderr.info('Print QC report at {0:s}'.format('report.txt'))
        report_fh = open('report.txt', 'wb')

    if args.statistic:
        logger_stderr.info('Print QC statistic report at {0:s}'.format(args.statistic))
        statistic_fh = open(args.statistic, 'wb')
    else:
        logger_stderr.info('Print QC statistic report at {0:s}'.format('statistic.txt'))
        statistic_fh = open('statistic.txt', 'wb')
    report_fh.write('Line_num\tError_code\tError_tag\n')
    for e in sorted(error_set):
        tag = '[{0:s}]'.format(e['eTag'])
        report_fh.write('{0:s}\t{1:s}\t{2:s}\n'.format(str(e['line_num']), str(e['eCode']), str(tag)))
    #statistic_file
    error_counts = dict()
    ERROR_INFO=ERROR.INFO
    statistic_fh.write('Error_code\tNumber_of_problematic_models\tError_tag\n')
    for s in sorted(error_set):
        if s['eCode'] not in error_counts:
            error_counts[s['eCode']]= {'count':0,'etag':ERROR_INFO[s['eCode']]}
        error_counts[s['eCode']]['count'] += 1   
    for a in error_counts:
        statistic_fh.write('{0:s}\t{1:s}\t{2:s}\n'.format(str(a),str(error_counts[a]['count']),str(error_counts[a]['etag'])))