#! /usr/local/bin/python2.7
# Copyright (C) 2015  Mei-Ju Chen <arbula [at] gmail [dot] com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""
Changelog:
"""

import sys
import re
import logging
# try to import from project first
from os.path import dirname
if dirname(__file__) == '':
    bin_path = '../lib'
else:
    bin_path = dirname(__file__) + '/../lib'
sys.path.insert(1, bin_path)
from gff3 import Gff3

__version__ = '0.0.1'


def PositionSort(linelist):
    id2line = {}
    id2start = {}
    seq2id = {}
    for line in linelist:
        id2line[str(line['line_raw'])] = line
        id2start[str(line['line_raw'])] = line['start']
        tmp = re.search('(.+?)(\d+)',line['seqid'])
        seqnum = tmp.groups()[1]
        if seq2id.has_key(seqnum):
            seq2id[seqnum].append(str(line['line_raw']))
        else:
            seq2id[seqnum] = [str(line['line_raw'])]
    keys = sorted(seq2id, key=lambda i: int(i))
    newlinelist=[]
    for k in keys:
        ids = seq2id[k]
        d = {}
        for ID in ids:
            d[ID] = id2start[ID]
        id_sorted = sorted(d, key=lambda i: int(d[i]))
        for i in id_sorted:
            newlinelist.append(id2line[i])
    return newlinelist

def StrandSort(linelist):
    strand = {}
    seq = {}
    id2line = {}
    id2start = {}
    id2end = {}
    for line in linelist:
        #print(line['attributes']['ID'])
        strand[line['strand']] = 0
        seq[line['seqid']] = 0
        id2line[str(line['line_raw'])] = line
        id2start[str(line['line_raw'])] = line['start']
        id2end[str(line['line_raw'])] = line['end']
    if not len(seq) == 1:
        print('Not all lines located in the same sequence. Cannot process by StrandSort.')
        return
    if not len(strand) == 1:
        print('Strand is not consistet among all lines in the list or strand information is missing. Cannot process by StrandSort.')
        return
    newlinelist=[]
    for k, v in strand.items():
        if k == '+':
            id_sorted = sorted(id2start, key=lambda i: int(id2start[i]))
            for i in id_sorted:
                newlinelist.append(id2line[i])
        elif k == '-':
            id_sorted = sorted(id2end, key=lambda i: int(id2end[i]), reverse=True)
            for i in id_sorted:
                newlinelist.append(id2line[i])
        else:
            print('Strand is not clear. Cannot process by StrandSort.')
    return newlinelist

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
    Sort a GFF3 file according to the order of Scaffold, coordinates on a Scaffold, and feature relationship based on sequence ontology.

    Inputs:
    1. GFF3 file: Specify the file name with the -g argument

    Outputs:
    1. Sorted GFF3 file: Specify the file name with the -og argument

    Examples:
    1. Specify the input, output file names and options using short arguments:
       python %(prog)s -g ../example/annotations.gff -og ../example/annotations_sorted.gff
    2. Specify the input, output file names and options using long arguments:
       python %(prog)s --gff_file ../example/annotations.gff --output_gff ../example/annotations_sorted.gff

    """))
    parser.add_argument('-g', '--gff_file', type=str, help='GFF3 file that you would like to sort.')
    parser.add_argument('-og', '--output_gff', type=str, help='Sorted GFF3 file')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    
 
    test_lv = 1 # debug
    if test_lv == 0:
        args = parser.parse_args(['-g', 'annotations.gff'])
    else:
        args = parser.parse_args()

    if args.gff_file:
        logger_stderr.info('Checking GFF3 file (%s)...', args.gff_file)
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.output_gff:
        report_fh = open(args.output_gff, 'wb')
    else:
        report_fh = sys.stdout

    logger_stderr.info('Reading gff3 file...')
    gff3 = Gff3(gff_file=args.gff_file, logger=logger_null)

    logger_stderr.info('Sorting and printing out...')
    roots = [line for line in gff3.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    roots_sorted = PositionSort(roots)
    report_fh.write('##gff-version 3\n')
    for root in roots_sorted:
        report_fh.write(root['line_raw'])
        children = root['children']
        children_sorted = PositionSort(children)
        otherlines=[]
        for child in children_sorted:
            #print('----------------')
            report_fh.write(child['line_raw'])
            grandchildren = child['children']
            gchildgroup = {}
            for grandchild in grandchildren:
                if gchildgroup.has_key(str(grandchild['type'])):
                    gchildgroup[str(grandchild['type'])].append(grandchild)
                else:
                    gchildgroup[str(grandchild['type'])] = []
                    gchildgroup[str(grandchild['type'])].append(grandchild)
                otherlines.extend(gff3.collect_descendants(grandchild))
            exons = []
            cdss = []
            others = []
            for k, v in gchildgroup.items():
                if k == 'exon' or k == 'pseudogenic_exon':
                    exons.extend(v)
                elif k == 'CDS':
                    cdss.extend(v)
                else:
                    others.extend(v)
            if len(exons):
                exons_sorted = StrandSort(exons)
                for exon in exons_sorted:
                    report_fh.write(exon['line_raw'])
            if len(cdss):
                cdss_sorted = StrandSort(cdss)
                for cds in cdss_sorted:
                    report_fh.write(cds['line_raw'])
            if len(others):
                for other in others:
                    report_fh.write(other['line_raw'])
        unique = {}
        for k in otherlines:
            unique[k['line_raw']] = 1
        for k,v in unique.items():
            report_fh.write(k)
        report_fh.write('###\n')
