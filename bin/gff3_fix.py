#! /usr/local/bin/python2.7
# Contributed by Li-Mei Chiang <dytk2134 [at] gmail [dot] com> (2017)
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
import version
if dirname(__file__) == '':
    lib_path = '../lib'
else:
    lib_path = dirname(__file__) + '/../lib'
sys.path.insert(1, lib_path)
sys.path =  filter (lambda a: not a.endswith('/bin'), sys.path)
from gff3_modified import Gff3
import gff3_fix

__version__ = version.__version__
   

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

    Input:
    1. Error report: Error report from gff3_QC.py. Specify the file name with the -qc_r or --qc_report argument;
    2. GFF3: Specify the file name with the -g or --gff argument;

    Output:
    1. Corrected GFF3


    Quick start:
    python2.7 bin/gff3_fix.py -qc_r error.txt -g example.gff3 -og corrected.gff3
    """))

    parser.add_argument('-qc_r', '--qc_report', type=str, help='Error report from gff3_QC.py')
    parser.add_argument('-g', '--gff', type=str, help='Genome annotation file, gff3 format')
    #parser.add_argument('-r', '--report', type=str, help='output report file name')
    parser.add_argument('-og', '--output_gff', type=str, help='output gff3 file name')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    args = parser.parse_args()
    logger_stderr.info('Reading QC report file: (%s)...\n', args.qc_report)
    #error_dict example: {'Emr0001': [[15,16],[13]],'Esf0005': [[17]]}
    error_dict = {}
    #line_num_dict example: {3: ['Emr0001','Esf0003'], 15: ['Emr0026']}
    line_num_dict = {}
    try:
        with open(args.qc_report, "r") as qcr:
            #ignore the first line (header)
            next(qcr)
            for line in qcr:
                line = line.strip()
                if line:
                    try:
                        lines = line.split("\t")
                        line_num_list = map(int,re.findall(r'\d+',lines[0]))
                        if lines[1] not in error_dict:
                            error_dict[lines[1]] = [line_num_list]
                        else:
                            error_dict[lines[1]].append(line_num_list)
                        for line_num in line_num_list:
                            if line_num not in line_num_dict:
                                line_num_dict[line_num] = {lines[1]: lines[2]}
                            else:
                                line_num_dict[line_num][lines[1]] = lines[2]
                    except:
                        logger_stderr.warning('Failed to recognize - %s', line)

    except:
        logger_stderr.error('Failed to read QC report file!')
    logger_stderr.info('Reading GFF3 file: (%s)...\n', args.gff)
    try:
        gff3 = Gff3(gff_file=args.gff, logger=logger_null)
    except:
        logger_stderr.error('Failed to read GFF3 file!')

    gff3_fix.fix.main(gff3=gff3, output_gff=args.output_gff, error_dict=error_dict, line_num_dict=line_num_dict, logger=logger_null)



                       
 

 
